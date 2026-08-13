"""Deterministic ASD-STE100 mechanical checker.

Counts violations a regex can catch: sentence length, contractions, banned
modals, perfect tenses, -ing clauses, semicolons, Latin abbreviations, slop
words, trailing conditions, synonym rotation, phrasal verbs, courtesy filler,
document deixis, and a few wordy constructions.

ponytail: regex, not a grammar parser. Undercounts (no reliable passive-voice
or part-of-speech check) and can miscount sentence bounds in unusual markdown.
Numbers are comparable between two texts run through this version. They are
not a compliance verdict. No tool can guarantee STE compliance.
"""
from __future__ import annotations

import re
from typing import Any

BANNED_MODALS = re.compile(r"\b(should|would|may|might|could)\b", re.I)
PERFECT = re.compile(r"\b(has|have|had)\s+been\b|\b(has|have)\s+\w+ed\b", re.I)
CONTRACTION = re.compile(
    r"\b\w+(n't|'ll|'re|'ve|'d)\b|\bit's\b|\byou're\b|\bwe're\b|\bthey're\b|\bthat's\b",
    re.I,
)
ING_CLAUSE = re.compile(
    r",\s*(mak|allow|enabl|ensur|highlight|creat|provid|offer|help|reduc|"
    r"improv|lead|caus|result)ing\b",
    re.I,
)
BY_ING = re.compile(r"\bBy\s+\w+ing\b")
LATIN = re.compile(r"\b(e\.g\.|i\.e\.|etc\.?|viz\.|vs\.)(?=[\s,)]|$)", re.I)
SLOP = re.compile(
    r"\b(simply|seamlessly|effortlessly|robust|leverag\w*|utiliz\w*|"
    r"comprehensive|powerful|blazingly|streamlin\w*|facilitat\w*|"
    r"performant|plethora|myriad|delve|crucial|pivotal|gracefully)\b",
    re.I,
)
TRAILING_COND = re.compile(r"\w[^.!?\n]{3,}\s\b(if|when)\b\s", re.I)
COURTESY = re.compile(r"\b(please|oops|kindly|feel free)\b", re.I)
ANDOR = re.compile(r"\band/or\b", re.I)
WORDY = re.compile(
    r"\b(in order to|prior to|in the event that|due to the fact that|as well as|"
    r"you'll want to|we recommend|please note|it should be noted|"
    r"it is worth noting|worth noting that)\b",
    re.I,
)
PHRASAL = re.compile(
    r"\b(set up|start up|shut down|turn on|turn off|carry out|look at|"
    r"find out|get rid of|deal with|fill in|fill out|work out|point out|"
    r"consist of|put in|take out|come back|go back|keep on|break down|"
    r"strip away|go down)\b",
    re.I,
)
DEIXIS = re.compile(r"\b(see above|the above|see below|as follows)\b", re.I)
MAKE_SURE = re.compile(r"\bmake sure\b(?!\s+that\b)", re.I)
EMDASH = re.compile(r"—")
SEMICOLON = re.compile(r";")
ROTATION_SETS = [
    ("check-verify", re.compile(r"\b(check|verify|confirm|validate|ensure)\w*\b", re.I)),
    ("config-settings", re.compile(r"\b(config|configuration|settings)\b", re.I)),
]
LIMITS = {"procedural": 20, "descriptive": 25}
NUMBER_UNIT = re.compile(
    r"\b\d[\d,.:]*\s*(%|ms|s|m|h|kg|g|mb|gb|tb|kb|hz|mhz|ghz|utc|v|a|w|px)?\b",
    re.I,
)

# Map internal keys to Issue 9 rule numbers (paraphrased; official wording is
# in the free standard at asd-ste100.org).
RULE_IDS = {
    "sentence_over_limit": "5.1/6.3",
    "paragraph_over_six": "6.6",
    "contraction": "4.2",
    "banned_modal": "3.2",
    "perfect_tense": "3.4",
    "ing_clause": "3.5",
    "by_ing": "3.5",
    "semicolon": "8.1",
    "em_dash": "8.1",
    "latin_abbrev": "GR-6",
    "slop_word": "1.3",
    "courtesy": "4.2",
    "and_or": "4.1",
    "wordy": "9.1",
    "phrasal_verb": "9.3",
    "document_deixis": "1.3",
    "make_sure_without_that": "GR-1",
    "trailing_condition": "5.4",
    "synonym_rotation": "1.11",
}

CHECKERS: list[tuple[str, re.Pattern[str]]] = [
    ("contraction", CONTRACTION),
    ("banned_modal", BANNED_MODALS),
    ("perfect_tense", PERFECT),
    ("ing_clause", ING_CLAUSE),
    ("by_ing", BY_ING),
    ("semicolon", SEMICOLON),
    ("em_dash", EMDASH),
    ("latin_abbrev", LATIN),
    ("slop_word", SLOP),
    ("courtesy", COURTESY),
    ("and_or", ANDOR),
    ("wordy", WORDY),
    ("phrasal_verb", PHRASAL),
    ("document_deixis", DEIXIS),
    ("make_sure_without_that", MAKE_SURE),
]


def strip_code(text: str) -> str:
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"`[^`\n]+`", " CODESPAN ", text)
    text = re.sub(r"^#+\s.*$", " ", text, flags=re.M)
    text = re.sub(r"https?://\S+", " URL ", text)
    return text


def normalize_for_count(text: str) -> str:
    return NUMBER_UNIT.sub(" NUMUNIT ", text)


def sentences(text: str) -> list[str]:
    text = re.sub(r"^\s*([-*]|\d+\.)\s+", "", text, flags=re.M)
    parts = re.split(r"(?<=[.!?:])\s+", text)
    return [p.strip() for p in parts if len(p.strip().split()) >= 2]


def word_count(sentence: str) -> int:
    return len(normalize_for_count(sentence).split())


def paragraph_offenders(text: str) -> list[tuple[int, int]]:
    """Return (offset, sentence count) for each paragraph above the six-sentence limit."""
    out: list[tuple[int, int]] = []
    pos = 0
    for block in re.split(r"\n\s*\n", text):
        idx = max(text.find(block, pos) if block else pos, 0)
        n = len(sentences(block))
        if n > 6:
            out.append((idx, n))
        pos = idx + len(block)
    return out


def paragraph_over_limit(text: str) -> int:
    return len(paragraph_offenders(text))


def _line_of(text: str, idx: int) -> int:
    return text[:idx].count("\n") + 1


def findings(text: str, text_type: str) -> list[dict[str, Any]]:
    """Line-level findings for SARIF, GitHub annotations, and the playground."""
    if text_type not in LIMITS:
        raise ValueError(f"unknown type {text_type!r} (procedural|descriptive)")
    body = strip_code(text)
    out: list[dict[str, Any]] = []
    for key, rx in CHECKERS:
        for m in rx.finditer(body):
            out.append(
                {
                    "rule": RULE_IDS[key],
                    "key": key,
                    "text": m.group(0),
                    "line": _line_of(body, m.start()),
                    "start": m.start(),
                    "end": m.end(),
                }
            )
    limit = LIMITS[text_type]
    for s in sentences(body):
        n = word_count(s)
        if n > limit:
            idx = body.find(s[:40]) if s else -1
            out.append(
                {
                    "rule": RULE_IDS["sentence_over_limit"],
                    "key": "sentence_over_limit",
                    "text": s[:120],
                    "line": _line_of(body, max(idx, 0)),
                    "words": n,
                    "limit": limit,
                }
            )
        if TRAILING_COND.search(s) and not re.match(r"^(if|when)\b", s, re.I):
            idx = body.find(s[:40]) if s else -1
            out.append(
                {
                    "rule": RULE_IDS["trailing_condition"],
                    "key": "trailing_condition",
                    "text": s[:120],
                    "line": _line_of(body, max(idx, 0)),
                }
            )
    for _, rx in ROTATION_SETS:
        stems = {m.group(1).lower().rstrip("s") for m in rx.finditer(body)}
        if len(stems) > 1:
            out.append(
                {
                    "rule": RULE_IDS["synonym_rotation"],
                    "key": "synonym_rotation",
                    "text": ", ".join(sorted(stems)),
                    "line": 1,
                }
            )
    for idx, n in paragraph_offenders(body):
        out.append(
            {
                "rule": RULE_IDS["paragraph_over_six"],
                "key": "paragraph_over_six",
                "text": f"{n} sentences in one paragraph (limit 6)",
                "line": _line_of(body, idx),
            }
        )
    out.sort(key=lambda f: (f.get("line", 0), f.get("key", "")))
    return out


def lint(text: str, text_type: str) -> dict[str, Any]:
    if text_type not in LIMITS:
        raise ValueError(f"unknown type {text_type!r} (procedural|descriptive)")
    body = strip_code(text)
    sents = sentences(body)
    limit = LIMITS[text_type]
    lengths = [word_count(s) for s in sents]
    counts: dict[str, int] = {}
    counts["sentence_over_limit"] = sum(1 for n in lengths if n > limit)
    counts["paragraph_over_six"] = paragraph_over_limit(body)
    for key, rx in CHECKERS:
        counts[key] = len(rx.findall(body))
    counts["trailing_condition"] = sum(
        1
        for s in sents
        if TRAILING_COND.search(s) and not re.match(r"^(if|when)\b", s, re.I)
    )
    rotation = 0
    for _, rx in ROTATION_SETS:
        stems = {m.group(1).lower().rstrip("s") for m in rx.finditer(body)}
        if len(stems) > 1:
            rotation += len(stems) - 1
    counts["synonym_rotation"] = rotation
    words = max(1, len(body.split()))
    total = sum(counts.values())
    hits = findings(text, text_type)
    return {
        "type": text_type,
        "words": words,
        "sentences": len(sents),
        "mean_sentence_words": round(sum(lengths) / max(1, len(lengths)), 1),
        "longest_sentence_words": max(lengths, default=0),
        "violations": counts,
        "violations_total": total,
        "violations_per_100w": round(100.0 * total / words, 2),
        "findings": hits,
        "disclaimer": (
            "No tool can guarantee ASD-STE100 compliance. "
            "Final approval rests with the writer. "
            "The official standard is a free download at asd-ste100.org."
        ),
    }


def format_report(result: dict[str, Any]) -> str:
    lines = [
        f"type: {result['type']}",
        f"words: {result['words']}",
        f"sentences: {result['sentences']}",
        f"mean sentence words: {result['mean_sentence_words']}",
        f"longest sentence words: {result['longest_sentence_words']}",
        f"violations total: {result['violations_total']}",
        f"violations per 100 words: {result['violations_per_100w']}",
        "by rule:",
    ]
    for key, n in result["violations"].items():
        if n:
            lines.append(f"  {key} ({RULE_IDS.get(key, '?')}): {n}")
    if result["violations_total"] == 0:
        lines.append("  (none)")
    lines.append(result["disclaimer"])
    return "\n".join(lines)


SLOP_FIXTURE = """Leveraging our robust retry mechanism, failed uploads are automatically
reattempted, ensuring data integrity is maintained throughout the entire process which has
been designed from the ground up to gracefully handle even the most challenging network
interruptions. You should verify your credentials; it's also worth checking the settings,
e.g. the timeout config. Contact support if the problem persists."""

SLOP_EXTRA = """Please set up the cluster in order to start. See above. Make sure the file exists.
By using the flag, you can turn on retries and/or logging — this is crucial."""

CLEAN_FIXTURE = """The system retries a failed upload automatically. This process keeps the data correct.

If failures continue, make sure that your credentials are correct. If the problem continues, contact support."""


def self_test() -> None:
    slop = lint(SLOP_FIXTURE, "procedural")
    extra = lint(SLOP_EXTRA, "procedural")
    clean = lint(CLEAN_FIXTURE, "procedural")
    assert slop["violations"]["sentence_over_limit"] >= 1, slop
    assert slop["violations"]["banned_modal"] >= 1, slop
    assert slop["violations"]["contraction"] >= 1, slop
    assert slop["violations"]["perfect_tense"] >= 1, slop
    assert slop["violations"]["ing_clause"] >= 1, slop
    assert slop["violations"]["semicolon"] == 1, slop
    assert slop["violations"]["latin_abbrev"] >= 1, slop
    assert slop["violations"]["slop_word"] >= 2, slop
    assert slop["violations"]["trailing_condition"] >= 1, slop
    assert slop["violations"]["synonym_rotation"] >= 1, slop
    assert extra["violations"]["courtesy"] >= 1, extra
    assert extra["violations"]["phrasal_verb"] >= 1, extra
    assert extra["violations"]["and_or"] >= 1, extra
    assert extra["violations"]["em_dash"] >= 1, extra
    assert extra["violations"]["by_ing"] >= 1, extra
    assert extra["violations"]["document_deixis"] >= 1, extra
    assert extra["violations"]["make_sure_without_that"] >= 1, extra
    assert extra["violations"]["wordy"] >= 1, extra
    assert clean["violations_total"] == 0, clean
    assert slop["findings"], "findings must be non-empty for slop"
    print(
        "self-test OK:",
        slop["violations_total"],
        "violations in slop fixture,",
        extra["violations_total"],
        "in extra fixture, 0 in clean,",
        len(slop["findings"]),
        "findings",
    )
