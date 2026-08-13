"""OneRead Intermediate Representation (ORIR).

The thing a prompt cannot be: a structured document that a compiler
can type-check once and emit to many surfaces.

ORIR is JSON. A passage is procedural or descriptive. A sentence carries its
word count (Rule 8.6), its violations, and a protected-token list. Emitters
read ORIR. They do not re-parse prose.

Schema: schema/orir.schema.json
"""
from __future__ import annotations

import re
from typing import Any

from .lint import LIMITS, lint, sentences, strip_code, word_count

ORIR_VERSION = "1.0"

CODE_SPAN = re.compile(r"`[^`\n]+`")
FENCE = re.compile(r"```.*?```", re.S)
HEADING = re.compile(r"^(#{1,6})\s+(.*)$", re.M)


def _protected(text: str) -> list[str]:
    tokens = CODE_SPAN.findall(text)
    tokens += re.findall(r"https?://\S+", text)
    return tokens


def _kind_for(sentence: str, default: str) -> str:
    if re.match(
        r"^(if|when|do not|make sure|set|run|install|stop|start|open|close|"
        r"click|press|type|copy|paste|send|get|put|delete|remove|add)\b",
        sentence,
        re.I,
    ):
        return "procedural"
    return default


def to_ir(text: str, text_type: str = "descriptive", source: str = "") -> dict[str, Any]:
    """Lower prose to ORIR. `text_type` is the default kind for unclassified sentences."""
    if text_type not in LIMITS:
        raise ValueError(f"unknown type {text_type!r}")
    report = lint(text, text_type)
    passages: list[dict[str, Any]] = []
    blocks = re.split(r"\n\s*\n", text.strip()) if text.strip() else []
    for i, block in enumerate(blocks, 1):
        if FENCE.search(block) or block.strip().startswith("#"):
            passages.append(
                {
                    "id": f"p{i}",
                    "kind": "protected",
                    "raw": block,
                    "sentences": [],
                }
            )
            continue
        sents = sentences(strip_code(block)) or ([block.strip()] if block.strip() else [])
        items = []
        kinds = []
        for s in sents:
            kind = _kind_for(s, text_type)
            kinds.append(kind)
            items.append(
                {
                    "text": s,
                    "kind": kind,
                    "words": word_count(s),
                    "limit": LIMITS[kind] if kind in LIMITS else LIMITS[text_type],
                    "protected": _protected(s),
                }
            )
        kind = "procedural" if kinds and all(k == "procedural" for k in kinds) else (
            "descriptive" if kinds and all(k == "descriptive" for k in kinds) else "mixed"
        )
        passages.append({"id": f"p{i}", "kind": kind, "raw": block, "sentences": items})
    headings = [{"level": len(m.group(1)), "text": m.group(2).strip()} for m in HEADING.finditer(text)]
    return {
        "orir": ORIR_VERSION,
        "source": source,
        "default_type": text_type,
        "headings": headings,
        "passages": passages,
        "lint": {
            "violations_total": report["violations_total"],
            "violations_per_100w": report["violations_per_100w"],
            "violations": report["violations"],
            "words": report["words"],
            "sentences": report["sentences"],
            "longest_sentence_words": report["longest_sentence_words"],
        },
        "findings": report["findings"],
        "disclaimer": report["disclaimer"],
    }
