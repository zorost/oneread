/* OneRead browser front end. Mirrors src/oneread/lint.py and src/oneread/compile.py.
   Regex, not a grammar parser. Not a compliance verdict.
   Rule keys here are checked against the Python rule table by tests/test_oneread.py. */
(function (root) {
  const LIMITS = { procedural: 20, descriptive: 25 };
  const MARK_IN = "\u0001";
  const MARK_OUT = "\u0002";
  const HOLD = "\u0000";
  const CAP = "\u0003";
  const SENT_START = /(?:^\s*|[.!?:]\s+|\n\s*)$/;
  const CAP_NEXT = /\u0003([\s\u0001]*)(\w)/g;

  const CHECKS = [
    ["contraction", /\b\w+(n't|'ll|'re|'ve|'d)\b|\bit's\b|\byou're\b|\bwe're\b|\bthey're\b|\bthat's\b/gi, "4.2"],
    ["banned_modal", /\b(should|would|may|might|could)\b/gi, "3.2"],
    ["perfect_tense", /\b(has|have|had)\s+been\b|\b(has|have)\s+\w+ed\b/gi, "3.4"],
    ["ing_clause", /,\s*(mak|allow|enabl|ensur|highlight|creat|provid|offer|help|reduc|improv|lead|caus|result)ing\b/gi, "3.5"],
    ["by_ing", /\bBy\s+\w+ing\b/g, "3.5"],
    ["semicolon", /;/g, "8.1"],
    ["em_dash", /—/g, "8.1"],
    ["latin_abbrev", /\b(e\.g\.|i\.e\.|etc\.?|viz\.|vs\.)(?=[\s,)]|$)/gi, "GR-6"],
    ["slop_word", /\b(simply|seamlessly|effortlessly|robust|leverag\w*|utiliz\w*|comprehensive|powerful|blazingly|streamlin\w*|facilitat\w*|performant|plethora|myriad|delve|crucial|pivotal|gracefully)\b/gi, "1.3"],
    ["courtesy", /\b(please|oops|kindly|feel free)\b/gi, "4.2"],
    ["and_or", /\band\/or\b/gi, "4.1"],
    ["wordy", /\b(in order to|prior to|in the event that|due to the fact that|as well as|you'll want to|we recommend|please note|it should be noted|it is worth noting|worth noting that)\b/gi, "9.1"],
    ["phrasal_verb", /\b(set up|start up|shut down|turn on|turn off|carry out|look at|find out|get rid of|deal with|fill in|fill out|work out|point out|consist of|put in|take out|come back|go back|keep on|break down|strip away|go down)\b/gi, "9.3"],
    ["document_deixis", /\b(see above|the above|see below|as follows)\b/gi, "1.3"],
    ["make_sure_without_that", /\bmake sure\b(?!\s+that\b)/gi, "GR-1"],
  ];

  const ROTATION_SETS = [
    /\b(check|verify|confirm|validate|ensure)\w*\b/gi,
    /\b(config|configuration|settings)\b/gi,
  ];
  const TRAILING_COND = /\w[^.!?\n]{3,}\s\b(if|when)\b\s/i;

  const RULE_IDS = {
    "sentence_over_limit": "5.1/6.3",
    "paragraph_over_six": "6.6",
    "trailing_condition": "5.4",
    "synonym_rotation": "1.11",
  };
  CHECKS.forEach(function (c) { RULE_IDS[c[0]] = c[2]; });

  /* Semantic rewrites a regex cannot prove. The compiler reports them, it does not guess. */
  const NEEDS_MODEL = [
    "sentence_over_limit",
    "banned_modal",
    "perfect_tense",
    "ing_clause",
    "by_ing",
    "trailing_condition",
    "synonym_rotation",
    "paragraph_over_six",
  ];

  const FENCE = /```[\s\S]*?```/g;
  const CODE = /`[^`\n]+`/g;
  const URL = /https?:\/\/\S+/g;

  const CONTRACTIONS = [
    [/\bit's\b/gi, "it is"],
    [/\byou're\b/gi, "you are"],
    [/\bwe're\b/gi, "we are"],
    [/\bthey're\b/gi, "they are"],
    [/\bthat's\b/gi, "that is"],
    [/\bwon't\b/gi, "will not"],
    [/\bcan't\b/gi, "cannot"],
    [/\bdon't\b/gi, "do not"],
    [/\bdoesn't\b/gi, "does not"],
    [/\bisn't\b/gi, "is not"],
    [/\baren't\b/gi, "are not"],
    [/\bwasn't\b/gi, "was not"],
    [/\bweren't\b/gi, "were not"],
    [/\bhaven't\b/gi, "have not"],
    [/\bhasn't\b/gi, "has not"],
    [/\bhadn't\b/gi, "had not"],
    [/\byou'll\b/gi, "you will"],
    [/\bwe'll\b/gi, "we will"],
    [/\bI'll\b/g, "I will"],
    [/\blet's\b/gi, "let us"],
    [/\byou've\b/gi, "you have"],
    [/\bwe've\b/gi, "we have"],
    [/\bthey've\b/gi, "they have"],
    [/\byou'd\b/gi, "you would"],
    [/\bwe'd\b/gi, "we would"],
    [/\bthey'd\b/gi, "they would"],
    [/\bdidn't\b/gi, "did not"],
    [/\bcouldn't\b/gi, "could not"],
    [/\bwouldn't\b/gi, "would not"],
    [/\bshouldn't\b/gi, "should not"],
    [/\bmustn't\b/gi, "must not"],
    [/\bneedn't\b/gi, "need not"],
    [/\bit'll\b/gi, "it will"],
    [/\bthey'll\b/gi, "they will"],
    [/\bthere's\b/gi, "there is"],
    [/\bhere's\b/gi, "here is"],
    [/\bwhat's\b/gi, "what is"],
    [/\bI'm\b/g, "I am"],
    [/\bI've\b/g, "I have"],
  ];

  const PHRASES = [
    [/\be\.g\.\s*/gi, "for example "],
    [/\bi\.e\.\s*/gi, "that is "],
    [/\betc\.\b/gi, ""],
    [/\bin order to\b/gi, "to"],
    [/\bprior to\b/gi, "before"],
    [/\bin the event that\b/gi, "if"],
    [/\bdue to the fact that\b/gi, "because"],
    [/\bas well as\b/gi, "and"],
    [/\ba (?:plethora|myriad) of\b/gi, "many"],
    [/\byou'll want to\b/gi, ""],
    [/\bplease note that\b/gi, ""],
    [/\bit should be noted that\b/gi, ""],
    [/\bwe recommend that you\b/gi, ""],
    [/\bplease\b/gi, ""],
    [/\boops\b!?\s*/gi, ""],
    [/\bkindly\b/gi, ""],
    [/\bfeel free to\b/gi, ""],
    [/\band\/or\b/gi, "or"],
    [/\bmake sure\b(?!\s+that\b)/gi, "make sure that"],
    [/\bset up\b/gi, "configure"],
    [/\bcarry out\b/gi, "do"],
    [/\bfind out\b/gi, "determine"],
    /* Keep the verb form the writer used. "By leveraging" is not "By use". */
    [/\bleveraging\b/gi, "using"],
    [/\bleveraged\b/gi, "used"],
    [/\bleverages\b/gi, "uses"],
    [/\bleverage\b/gi, "use"],
    [/\butilizing\b/gi, "using"],
    [/\butilized\b/gi, "used"],
    [/\butilizes\b/gi, "uses"],
    [/\butilize\b/gi, "use"],
    [/—/g, ". "],
    [/;/g, ". "],
  ];

  /* An adverb of enthusiasm carries no information. It always goes. */
  const SLOP_ADVERB = /\b(simply|seamlessly|effortlessly|blazingly|gracefully)\b,?\s*/gi;
  /* An adjective of enthusiasm goes only where it modifies a noun. */
  const SLOP_ADJECTIVE = /\b(robust|comprehensive|powerful|performant|crucial|pivotal)\b,?\s*/gi;
  const BE_COMPLEMENT = /\b(?:is|are|was|were|be|been|being|seems?|remains?)\s+$/i;

  /* After a be-verb the adjective is the predicate. Deleting it leaves "is .". */
  function slopAdjective(m, before) {
    return BE_COMPLEMENT.test(before) ? m : "";
  }

  function stripCode(text) {
    return text
      .replace(/```[\s\S]*?```/g, " ")
      .replace(/`[^`\n]+`/g, " CODESPAN ")
      .replace(/^#+\s.*$/gm, " ")
      .replace(/https?:\/\/\S+/g, " URL ");
  }

  function sentences(text) {
    const cleaned = text.replace(/^\s*([-*]|\d+\.)\s+/gm, "");
    return cleaned
      .split(/(?<=[.!?:])\s+/)
      .map(function (s) { return s.trim(); })
      .filter(function (s) { return s.split(/\s+/).length >= 2; });
  }

  function wordCount(s) {
    return s
      .replace(/\b\d[\d,.:]*\s*(%|ms|s|m|h|kg|g|mb|gb|tb|kb|hz|mhz|ghz|utc|v|a|w|px)?\b/gi, " NUMUNIT ")
      .trim()
      .split(/\s+/).filter(Boolean).length;
  }

  function lineOf(text, index) {
    return text.slice(0, Math.max(0, index)).split("\n").length;
  }

  function paragraphOffenders(body) {
    const out = [];
    let pos = 0;
    body.split(/\n\s*\n/).forEach(function (block) {
      const idx = Math.max(block ? body.indexOf(block, pos) : pos, 0);
      const n = sentences(block).length;
      if (n > 6) out.push({ index: idx, count: n });
      pos = idx + block.length;
    });
    return out;
  }

  function rotationStems(body, rx) {
    const iter = new RegExp(rx.source, rx.flags);
    const stems = {};
    let m;
    while ((m = iter.exec(body))) {
      stems[m[1].toLowerCase().replace(/s+$/, "")] = true;
    }
    return Object.keys(stems).sort();
  }

  function lint(text, type) {
    const kind = LIMITS[type] ? type : "descriptive";
    const body = stripCode(text);
    const sents = sentences(body);
    const limit = LIMITS[kind];
    const paragraphs = paragraphOffenders(body);
    const violations = { sentence_over_limit: 0, paragraph_over_six: paragraphs.length };
    const findings = [];
    CHECKS.forEach(function (check) {
      const key = check[0];
      const iter = new RegExp(check[1].source, check[1].flags);
      let m;
      let n = 0;
      while ((m = iter.exec(body))) {
        n += 1;
        findings.push({ key: key, rule: check[2], text: m[0], line: lineOf(body, m.index) });
      }
      violations[key] = n;
    });
    violations.trailing_condition = 0;
    let longest = 0;
    sents.forEach(function (s) {
      const n = wordCount(s);
      const at = lineOf(body, body.indexOf(s.slice(0, 40)));
      if (n > longest) longest = n;
      if (n > limit) {
        violations.sentence_over_limit += 1;
        findings.push({ key: "sentence_over_limit", rule: RULE_IDS.sentence_over_limit, text: s.slice(0, 120), words: n, limit: limit, line: at });
      }
      if (TRAILING_COND.test(s) && !/^(if|when)\b/i.test(s)) {
        violations.trailing_condition += 1;
        findings.push({ key: "trailing_condition", rule: RULE_IDS.trailing_condition, text: s.slice(0, 120), line: at });
      }
    });
    let rotation = 0;
    ROTATION_SETS.forEach(function (rx) {
      const stems = rotationStems(body, rx);
      if (stems.length > 1) {
        rotation += stems.length - 1;
        findings.push({ key: "synonym_rotation", rule: RULE_IDS.synonym_rotation, text: stems.join(", "), line: 1 });
      }
    });
    violations.synonym_rotation = rotation;
    paragraphs.forEach(function (p) {
      findings.push({ key: "paragraph_over_six", rule: RULE_IDS.paragraph_over_six, text: p.count + " sentences in one paragraph (limit 6)", line: lineOf(body, p.index) });
    });
    findings.sort(function (a, b) { return a.line - b.line || (a.key < b.key ? -1 : a.key > b.key ? 1 : 0); });
    const words = Math.max(1, body.trim().split(/\s+/).filter(Boolean).length);
    let total = 0;
    Object.keys(violations).forEach(function (k) { total += violations[k]; });
    return {
      type: kind,
      words: words,
      sentences: sents.length,
      longest: longest,
      limit: limit,
      violations: violations,
      violations_total: total,
      violations_per_100w: Math.round((10000 * total) / words) / 100,
      findings: findings,
    };
  }

  /* Returns the compiled text, the same text with rewritten spans marked, and the
     residual report. A rewrite the compiler cannot prove is reported, never guessed. */
  function compile(text, type) {
    const before = lint(text, type);
    const held = [];
    function hold(m) {
      held.push(m);
      return HOLD + "H" + (held.length - 1) + HOLD;
    }
    let work = text.replace(FENCE, hold).replace(CODE, hold).replace(URL, hold);
    const rewrites = [];
    function apply(rx, repl) {
      work = work.replace(new RegExp(rx.source, rx.flags), function () {
        const m = arguments[0];
        const offset = arguments[arguments.length - 2];
        const before = arguments[arguments.length - 1].slice(0, offset);
        const out = typeof repl === "function" ? repl(m, before) : repl;
        if (out === m) return m;
        const core = out.trim();
        rewrites.push({ from: m.trim(), to: core });
        const atStart = SENT_START.test(before);
        if (!core) return atStart ? CAP : "";
        const head = atStart ? core.charAt(0).toUpperCase() + core.slice(1) : core;
        return out.match(/^\s*/)[0] + MARK_IN + head + MARK_OUT + out.match(/\s*$/)[0];
      });
    }
    CONTRACTIONS.forEach(function (p) { apply(p[0], p[1]); });
    PHRASES.forEach(function (p) { apply(p[0], p[1]); });
    apply(SLOP_ADVERB, "");
    apply(SLOP_ADJECTIVE, slopAdjective);
    work = work
      .replace(CAP_NEXT, function (m, gap, ch) { return gap + ch.toUpperCase(); })
      .split(CAP).join("");
    work = work.replace(/[ \t]{2,}/g, " ").replace(/ +\n/g, "\n").replace(/\n{3,}/g, "\n\n");
    held.forEach(function (tok, i) {
      work = work.replace(HOLD + "H" + i + HOLD, function () { return tok; });
    });
    const marked = work.trim();
    const compiled = marked.split(MARK_IN).join("").split(MARK_OUT).join("");
    const after = lint(compiled, type);
    const needs = NEEDS_MODEL.filter(function (k) { return after.violations[k]; });
    return {
      text: compiled,
      marked: marked,
      rewrites: rewrites,
      before: before,
      after: after,
      needs_model: needs,
    };
  }

  root.OneRead = { lint: lint, compile: compile, LIMITS: LIMITS, RULE_IDS: RULE_IDS, NEEDS_MODEL: NEEDS_MODEL, MARK_IN: MARK_IN, MARK_OUT: MARK_OUT };
})(window);
