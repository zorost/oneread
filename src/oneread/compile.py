"""Mechanical compile pass.

A prompt can rewrite anything. A compiler can only rewrite what it can prove.
OneRead compiles the mechanical subset (contractions, Latin abbreviations,
courtesy filler, wordy phrases, semicolons, em dashes, missing "that" after
make sure) and leaves semantic rewrites (voice, one-instruction-per-sentence,
condition-first) marked as needs-model.

Protected tokens (code spans, fences, URLs) are never touched.
"""
from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any

from .ir import to_ir
from .lint import lint

FENCE = re.compile(r"```.*?```", re.S)
CODE = re.compile(r"`[^`\n]+`")
URL = re.compile(r"https?://\S+")

CONTRACTIONS = [
    (re.compile(r"\bit's\b", re.I), "it is"),
    (re.compile(r"\byou're\b", re.I), "you are"),
    (re.compile(r"\bwe're\b", re.I), "we are"),
    (re.compile(r"\bthey're\b", re.I), "they are"),
    (re.compile(r"\bthat's\b", re.I), "that is"),
    (re.compile(r"\bwon't\b", re.I), "will not"),
    (re.compile(r"\bcan't\b", re.I), "cannot"),
    (re.compile(r"\bdon't\b", re.I), "do not"),
    (re.compile(r"\bdoesn't\b", re.I), "does not"),
    (re.compile(r"\bisn't\b", re.I), "is not"),
    (re.compile(r"\baren't\b", re.I), "are not"),
    (re.compile(r"\bwasn't\b", re.I), "was not"),
    (re.compile(r"\bweren't\b", re.I), "were not"),
    (re.compile(r"\bhaven't\b", re.I), "have not"),
    (re.compile(r"\bhasn't\b", re.I), "has not"),
    (re.compile(r"\bhadn't\b", re.I), "had not"),
    (re.compile(r"\byou'll\b", re.I), "you will"),
    (re.compile(r"\bwe'll\b", re.I), "we will"),
    (re.compile(r"\bI'll\b"), "I will"),
    (re.compile(r"\blet's\b", re.I), "let us"),
    (re.compile(r"\byou've\b", re.I), "you have"),
    (re.compile(r"\bwe've\b", re.I), "we have"),
    (re.compile(r"\bthey've\b", re.I), "they have"),
    (re.compile(r"\byou'd\b", re.I), "you would"),
    (re.compile(r"\bwe'd\b", re.I), "we would"),
    (re.compile(r"\bthey'd\b", re.I), "they would"),
    (re.compile(r"\bdidn't\b", re.I), "did not"),
    (re.compile(r"\bcouldn't\b", re.I), "could not"),
    (re.compile(r"\bwouldn't\b", re.I), "would not"),
    (re.compile(r"\bshouldn't\b", re.I), "should not"),
    (re.compile(r"\bmustn't\b", re.I), "must not"),
    (re.compile(r"\bneedn't\b", re.I), "need not"),
    (re.compile(r"\bit'll\b", re.I), "it will"),
    (re.compile(r"\bthey'll\b", re.I), "they will"),
    (re.compile(r"\bthere's\b", re.I), "there is"),
    (re.compile(r"\bhere's\b", re.I), "here is"),
    (re.compile(r"\bwhat's\b", re.I), "what is"),
    (re.compile(r"\bI'm\b"), "I am"),
    (re.compile(r"\bI've\b"), "I have"),
]

PHRASES = [
    (re.compile(r"\be\.g\.\s*", re.I), "for example "),
    (re.compile(r"\bi\.e\.\s*", re.I), "that is "),
    (re.compile(r"\betc\.\b", re.I), ""),
    (re.compile(r"\bin order to\b", re.I), "to"),
    (re.compile(r"\bprior to\b", re.I), "before"),
    (re.compile(r"\bin the event that\b", re.I), "if"),
    (re.compile(r"\bdue to the fact that\b", re.I), "because"),
    (re.compile(r"\bas well as\b", re.I), "and"),
    (re.compile(r"\ba (?:plethora|myriad) of\b", re.I), "many"),
    (re.compile(r"\byou'll want to\b", re.I), ""),
    (re.compile(r"\bplease note that\b", re.I), ""),
    (re.compile(r"\bit should be noted that\b", re.I), ""),
    (re.compile(r"\bwe recommend that you\b", re.I), ""),
    (re.compile(r"\bplease\b", re.I), ""),
    (re.compile(r"\boops\b!?\s*", re.I), ""),
    (re.compile(r"\bkindly\b", re.I), ""),
    (re.compile(r"\bfeel free to\b", re.I), ""),
    (re.compile(r"\band/or\b", re.I), "or"),
    (re.compile(r"\bmake sure\b(?!\s+that\b)", re.I), "make sure that"),
    (re.compile(r"\bset up\b", re.I), "configure"),
    (re.compile(r"\bcarry out\b", re.I), "do"),
    (re.compile(r"\bfind out\b", re.I), "determine"),
    # Keep the verb form the writer used. "By leveraging" is not "By use".
    (re.compile(r"\bleveraging\b", re.I), "using"),
    (re.compile(r"\bleveraged\b", re.I), "used"),
    (re.compile(r"\bleverages\b", re.I), "uses"),
    (re.compile(r"\bleverage\b", re.I), "use"),
    (re.compile(r"\butilizing\b", re.I), "using"),
    (re.compile(r"\butilized\b", re.I), "used"),
    (re.compile(r"\butilizes\b", re.I), "uses"),
    (re.compile(r"\butilize\b", re.I), "use"),
    (re.compile(r"—"), ". "),
    (re.compile(r";"), ". "),
]

# An adverb of enthusiasm carries no information. It always goes.
SLOP_ADVERB = re.compile(
    r"\b(simply|seamlessly|effortlessly|blazingly|gracefully)\b,?\s*", re.I
)
# An adjective of enthusiasm goes only where it modifies a noun.
SLOP_ADJECTIVE = re.compile(
    r"\b(robust|comprehensive|powerful|performant|crucial|pivotal)\b,?\s*", re.I
)
BE_COMPLEMENT = re.compile(r"\b(?:is|are|was|were|be|been|being|seems?|remains?)\s+$", re.I)


def _slop_adjective(m: re.Match[str]) -> str:
    """After a be-verb the adjective is the predicate. Deleting it leaves "is ."."""
    if BE_COMPLEMENT.search(m.string[: m.start()]):
        return m.group(0)
    return ""

CAP = "\x03"
SENT_START = re.compile(r"(?:\A\s*|[.!?:]\s+|\n\s*)\Z")
CAP_NEXT = re.compile(CAP + r"(\s*)(\w)")

NEEDS_MODEL = {
    "sentence_over_limit",
    "banned_modal",
    "perfect_tense",
    "ing_clause",
    "by_ing",
    "trailing_condition",
    "synonym_rotation",
    "paragraph_over_six",
}


def _protect(text: str) -> tuple[str, list[str]]:
    held: list[str] = []

    def hold(m: re.Match[str]) -> str:
        held.append(m.group(0))
        return f"\x00H{len(held) - 1}\x00"

    text = FENCE.sub(hold, text)
    text = CODE.sub(hold, text)
    text = URL.sub(hold, text)
    return text, held


def _restore(text: str, held: list[str]) -> str:
    for i, tok in enumerate(held):
        text = text.replace(f"\x00H{i}\x00", tok)
    return text


def _sub(work: str, rx: re.Pattern[str], repl: str | Callable[[re.Match[str]], str]) -> str:
    """Substitute, and keep the sentence-initial capital the writer wrote.

    A deletion at a sentence start leaves a marker so the word that becomes the
    new first word is capitalized once every rule has run.
    """

    def go(m: re.Match[str]) -> str:
        text = repl(m) if callable(repl) else repl
        if text == m.group(0):
            return text
        at_start = SENT_START.search(m.string[: m.start()]) is not None
        if not text.strip():
            return CAP if at_start else text
        if at_start:
            return text[:1].upper() + text[1:]
        return text

    return rx.sub(go, work)


def compile_text(text: str, text_type: str = "descriptive") -> dict[str, Any]:
    """Return compiled prose plus a residual lint report and needs-model keys."""
    before = lint(text, text_type)
    work, held = _protect(text)
    for rx, repl in CONTRACTIONS:
        work = _sub(work, rx, repl)
    for rx, repl in PHRASES:
        work = _sub(work, rx, repl)
    work = _sub(work, SLOP_ADVERB, "")
    work = _sub(work, SLOP_ADJECTIVE, _slop_adjective)
    work = CAP_NEXT.sub(lambda m: m.group(1) + m.group(2).upper(), work)
    work = work.replace(CAP, "")
    work = re.sub(r"[ \t]{2,}", " ", work)
    work = re.sub(r" +\n", "\n", work)
    work = re.sub(r"\n{3,}", "\n\n", work)
    compiled = _restore(work, held).strip() + ("\n" if text.endswith("\n") else "")
    after = lint(compiled, text_type)
    residual = [k for k, n in after["violations"].items() if n and k in NEEDS_MODEL]
    return {
        "source": text,
        "compiled": compiled,
        "before": {
            "violations_total": before["violations_total"],
            "violations_per_100w": before["violations_per_100w"],
        },
        "after": {
            "violations_total": after["violations_total"],
            "violations_per_100w": after["violations_per_100w"],
            "violations": after["violations"],
        },
        "needs_model": residual,
        "ir": to_ir(compiled, text_type),
        "disclaimer": after["disclaimer"],
    }
