/* OneRead browser linter. Same mechanical rules as src/oneread/lint.py.
   Regex, not a grammar parser. Not a compliance verdict. */
(function (root) {
  const LIMITS = { procedural: 20, descriptive: 25 };
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
    ["wordy", /\b(in order to|prior to|in the event that|due to the fact that|as well as|you'll want to|we recommend|please note|it should be noted)\b/gi, "9.1"],
    ["phrasal_verb", /\b(set up|start up|shut down|turn on|turn off|carry out|look at|find out|get rid of|deal with|fill in|fill out|work out|point out|consist of|put in|take out|come back|go back|keep on|break down|strip away|go down)\b/gi, "9.3"],
    ["document_deixis", /\b(see above|the above|see below|as follows)\b/gi, "1.3"],
    ["make_sure_without_that", /\bmake sure\b(?!\s+that\b)/gi, "GR-1"],
  ];

  function stripCode(text) {
    return text
      .replace(/```[\s\S]*?```/g, " ")
      .replace(/`[^`\n]+`/g, " CODESPAN ")
      .replace(/^#+\s.*$/gm, " ")
      .replace(/https?:\/\/\S+/g, " URL ");
  }

  function sentences(text) {
    const cleaned = text.replace(/^\s*([-*]|\d+\.)\s+/gm, "");
    return cleaned.split(/(?<=[.!?:])\s+/).filter((s) => s.trim().split(/\s+/).length >= 2);
  }

  function wordCount(s) {
    return s
      .replace(/\b\d[\d,.:]*\s*(%|ms|s|m|h|kg|g|mb|gb|tb|kb|hz|mhz|ghz|utc|v|a|w|px)?\b/gi, " NUMUNIT ")
      .trim()
      .split(/\s+/).filter(Boolean).length;
  }

  function lint(text, type) {
    const body = stripCode(text);
    const sents = sentences(body);
    const limit = LIMITS[type] || 25;
    const violations = {};
    const findings = [];
    CHECKS.forEach(([key, rx, rule]) => {
      const copy = new RegExp(rx.source, rx.flags);
      const hits = body.match(copy) || [];
      violations[key] = hits.length;
      const iter = new RegExp(rx.source, rx.flags);
      let m;
      while ((m = iter.exec(body))) {
        findings.push({ key, rule, text: m[0], index: m.index });
      }
    });
    violations.sentence_over_limit = 0;
    violations.trailing_condition = 0;
    sents.forEach((s) => {
      const n = wordCount(s);
      if (n > limit) {
        violations.sentence_over_limit += 1;
        findings.push({ key: "sentence_over_limit", rule: "5.1/6.3", text: s.slice(0, 120), words: n, limit });
      }
      if (/\w[^.!?\n]{3,}\s\b(if|when)\b\s/i.test(s) && !/^(if|when)\b/i.test(s)) {
        violations.trailing_condition += 1;
        findings.push({ key: "trailing_condition", rule: "5.4", text: s.slice(0, 120) });
      }
    });
    const words = Math.max(1, body.trim().split(/\s+/).filter(Boolean).length);
    const total = Object.values(violations).reduce((a, b) => a + b, 0);
    return {
      type,
      words,
      sentences: sents.length,
      longest: sents.reduce((m, s) => Math.max(m, wordCount(s)), 0),
      violations,
      violations_total: total,
      violations_per_100w: Math.round((1000 * total) / words) / 10,
      findings,
    };
  }

  function compile(text) {
    let work = text;
    const held = [];
    work = work.replace(/```[\s\S]*?```/g, (m) => {
      held.push(m);
      return `\0H${held.length - 1}\0`;
    });
    work = work.replace(/`[^`\n]+`/g, (m) => {
      held.push(m);
      return `\0H${held.length - 1}\0`;
    });
    const pairs = [
      [/\bit's\b/gi, "it is"],
      [/\byou're\b/gi, "you are"],
      [/\bthat's\b/gi, "that is"],
      [/\bdon't\b/gi, "do not"],
      [/\bcan't\b/gi, "cannot"],
      [/\bwon't\b/gi, "will not"],
      [/\byou'll\b/gi, "you will"],
      [/\be\.g\.\s*/gi, "for example "],
      [/\bi\.e\.\s*/gi, "that is "],
      [/\bin order to\b/gi, "to"],
      [/\bprior to\b/gi, "before"],
      [/\bin the event that\b/gi, "if"],
      [/\bplease\b/gi, ""],
      [/\boops!?\b/gi, ""],
      [/\band\/or\b/gi, "or"],
      [/\bmake sure\b(?!\s+that\b)/gi, "make sure that"],
      [/\bset up\b/gi, "configure"],
      [/—/g, ". "],
      [/;/g, ". "],
    ];
    pairs.forEach(([rx, repl]) => {
      work = work.replace(rx, repl);
    });
    work = work.replace(
      /\b(simply|seamlessly|effortlessly|robust|comprehensive|powerful|crucial|pivotal)\b,?\s*/gi,
      "",
    );
    held.forEach((tok, i) => {
      work = work.replace(`\0H${i}\0`, tok);
    });
    return work.replace(/[ \t]{2,}/g, " ").trim();
  }

  root.OneRead = { lint, compile, LIMITS };
})(window);
