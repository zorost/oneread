"""Emitters: one IR, many surfaces.

A skill stops at prose. OneRead compiles to ORIR, then renders:

  markdown   GitHub README, runbook, ADR
  html       docs site, WordPress body
  sarif      GitHub code scanning, VS Code
  github     workflow annotations
  slack      Block Kit runbook
  openapi    description / summary fields
  skill      SKILL.md body
  mcp        tool description
  rfc9457    Problem Details title + detail
  amm        aviation maintenance procedure skeleton
"""
from __future__ import annotations

import json
from typing import Any, Callable

from .ir import to_ir
from .lint import RULE_IDS, lint

EMITTERS = (
    "markdown",
    "html",
    "sarif",
    "github",
    "slack",
    "openapi",
    "skill",
    "mcp",
    "rfc9457",
    "amm",
)


def _sentences(ir: dict[str, Any]) -> list[str]:
    out = []
    for p in ir.get("passages", []):
        if p.get("kind") == "protected":
            out.append(p.get("raw", ""))
            continue
        for s in p.get("sentences", []):
            out.append(s["text"])
    return out


def emit_markdown(ir: dict[str, Any]) -> str:
    parts = []
    for p in ir.get("passages", []):
        if p.get("kind") == "protected":
            parts.append(p.get("raw", "").rstrip())
            continue
        sents = p.get("sentences") or []
        if p.get("kind") == "procedural" and len(sents) > 1:
            parts.append("\n".join(f"{i}. {s['text']}" for i, s in enumerate(sents, 1)))
        else:
            parts.append(" ".join(s["text"] for s in sents))
    body = "\n\n".join(p for p in parts if p)
    n = ir.get("lint", {}).get("violations_total", 0)
    note = (
        f"\n\n---\nOneRead residual findings: {n}. "
        "No tool can guarantee ASD-STE100 compliance. "
        "Official standard: https://www.asd-ste100.org/\n"
    )
    return body + note


def emit_html(ir: dict[str, Any]) -> str:
    chunks = ["<article class='oneread'>"]
    for p in ir.get("passages", []):
        if p.get("kind") == "protected":
            raw = p.get("raw", "")
            chunks.append(f"<pre><code>{_esc(raw)}</code></pre>")
            continue
        sents = p.get("sentences") or []
        if p.get("kind") == "procedural" and len(sents) > 1:
            items = "".join(f"<li>{_esc(s['text'])}</li>" for s in sents)
            chunks.append(f"<ol>{items}</ol>")
        else:
            chunks.append("<p>" + " ".join(_esc(s["text"]) for s in sents) + "</p>")
    chunks.append("</article>")
    return "\n".join(chunks)


def emit_sarif(ir: dict[str, Any], source: str = "input.md") -> str:
    results = []
    for f in ir.get("findings", []):
        results.append(
            {
                "ruleId": f.get("rule", f.get("key")),
                "level": "warning",
                "message": {"text": f"{f.get('key')}: {f.get('text', '')[:160]}"},
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {"uri": source},
                            "region": {"startLine": int(f.get("line") or 1)},
                        }
                    }
                ],
            }
        )
    doc = {
        "version": "2.1.0",
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "OneRead",
                        "version": "1.0.0",
                        "informationUri": "https://github.com/zorost/oneread",
                        "rules": [
                            {
                                "id": rid,
                                "shortDescription": {"text": key},
                                "helpUri": "https://www.asd-ste100.org/",
                            }
                            for key, rid in RULE_IDS.items()
                        ],
                    }
                },
                "results": results,
            }
        ],
    }
    return json.dumps(doc, indent=2)


def emit_github(ir: dict[str, Any]) -> str:
    lines = []
    for f in ir.get("findings", []):
        line = int(f.get("line") or 1)
        msg = f"{f.get('rule')}: {f.get('text', '')[:120]}".replace("\n", " ")
        lines.append(f"::warning file=input.md,line={line}::{msg}")
    if not lines:
        lines.append("::notice::OneRead found no mechanical STE violations.")
    return "\n".join(lines) + "\n"


def emit_slack(ir: dict[str, Any]) -> str:
    sents = _sentences(ir)
    blocks: list[dict[str, Any]] = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "OneRead runbook"},
        }
    ]
    for i, s in enumerate(sents, 1):
        blocks.append(
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*{i}.* {s}"},
            }
        )
    n = ir.get("lint", {}).get("violations_total", 0)
    blocks.append(
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Residual findings: {n}. Unofficial. asd-ste100.org",
                }
            ],
        }
    )
    return json.dumps({"blocks": blocks}, indent=2)


def emit_openapi(ir: dict[str, Any]) -> str:
    sents = [s for s in _sentences(ir) if s]
    summary = sents[0] if sents else ""
    if len(summary.split()) > 25:
        summary = " ".join(summary.split()[:24]) + "."
    description = "\n\n".join(sents)
    return json.dumps({"summary": summary, "description": description}, indent=2)


def emit_skill(ir: dict[str, Any]) -> str:
    body = emit_markdown(ir)
    return (
        "---\n"
        "name: oneread-output\n"
        "description: Procedure compiled by OneRead from ASD-STE100 mechanical rules.\n"
        "---\n\n"
        + body
    )


def emit_mcp(ir: dict[str, Any]) -> str:
    sents = [s for s in _sentences(ir) if s]
    desc = " ".join(sents[:4])
    return json.dumps(
        {
            "name": "oneread_procedure",
            "description": desc[:1024],
            "inputSchema": {
                "type": "object",
                "properties": {
                    "target": {
                        "type": "string",
                        "description": "The object this procedure acts on.",
                    }
                },
                "required": ["target"],
            },
        },
        indent=2,
    )


def emit_rfc9457(ir: dict[str, Any]) -> str:
    sents = [s for s in _sentences(ir) if s]
    title = sents[0] if sents else "The request failed."
    detail = " ".join(sents[1:3]) if len(sents) > 1 else title
    return json.dumps(
        {
            "type": "about:blank",
            "title": title[:120],
            "status": 400,
            "detail": detail,
        },
        indent=2,
    )


def emit_amm(ir: dict[str, Any]) -> str:
    """Aviation maintenance procedure skeleton. STE was built for this page."""
    sents = [s for s in _sentences(ir) if s]
    lines = [
        "TASK: (give the official task number from the AMM)",
        "",
        "WARNING: Isolate the energy source before you open the unit. Live voltage can kill you.",
        "",
        "CAUTION: Do not apply power until the test in this task is complete. Wrong power can damage the unit.",
        "",
        "PROCEDURE:",
    ]
    for i, s in enumerate(sents, 1):
        lines.append(f"{i}. {s}")
    lines += [
        "",
        "NOTE: A note gives information. It does not give a command.",
        "",
        "RESULT: The unit operates in the specified condition.",
        "",
        "OneRead cannot certify an AMM page. Use the official ASD-STE100 dictionary",
        "and the manufacturer publication spec. https://www.asd-ste100.org/",
    ]
    return "\n".join(lines) + "\n"


def _esc(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


_DISPATCH: dict[str, Callable[..., str]] = {
    "markdown": emit_markdown,
    "html": emit_html,
    "sarif": lambda ir, **kw: emit_sarif(ir, kw.get("source", "input.md")),
    "github": emit_github,
    "slack": emit_slack,
    "openapi": emit_openapi,
    "skill": emit_skill,
    "mcp": emit_mcp,
    "rfc9457": emit_rfc9457,
    "amm": emit_amm,
}


def emit(target: str, text: str | None = None, ir: dict[str, Any] | None = None,
         text_type: str = "descriptive", source: str = "input.md") -> str:
    if target not in _DISPATCH:
        raise ValueError(f"unknown emitter {target!r}. choose from: {', '.join(EMITTERS)}")
    if ir is None:
        if text is None:
            raise ValueError("pass text or ir")
        ir = to_ir(text, text_type, source=source)
        ir.setdefault("findings", lint(text, text_type)["findings"])
    fn = _DISPATCH[target]
    if target == "sarif":
        return fn(ir, source=source)
    return fn(ir)
