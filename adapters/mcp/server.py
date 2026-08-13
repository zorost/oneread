#!/usr/bin/env python3
"""Stdlib MCP server for OneRead.

Exposes three tools over MCP stdio JSON-RPC (protocol version 2024-11-05):

  oneread_lint      mechanical STE findings
  oneread_compile   mechanical rewrite + residual keys
  oneread_emit      compile then render one surface

No third-party MCP SDK. A host that speaks MCP stdio can call this process.
Unofficial. Not affiliated with ASD.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from oneread.compile import compile_text  # noqa: E402
from oneread.emit import EMITTERS, emit  # noqa: E402
from oneread.lint import lint  # noqa: E402

PROTOCOL = "2024-11-05"
TOOLS = [
    {
        "name": "oneread_lint",
        "description": (
            "Type-check technical English against ASD-STE100 Issue 9 mechanical "
            "rules. Returns violation counts and line-level findings. Unofficial. "
            "Does not certify compliance."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "type": {"type": "string", "enum": ["procedural", "descriptive"], "default": "descriptive"},
            },
            "required": ["text"],
        },
    },
    {
        "name": "oneread_compile",
        "description": (
            "Mechanically compile technical English (contractions, filler, Latin "
            "abbreviations, semicolons) and report residual findings that still "
            "need a model rewrite."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "type": {"type": "string", "enum": ["procedural", "descriptive"], "default": "descriptive"},
            },
            "required": ["text"],
        },
    },
    {
        "name": "oneread_emit",
        "description": (
            "Compile technical English and emit it to one surface: markdown, html, "
            "sarif, github, slack, openapi, skill, mcp, rfc9457, or amm."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "to": {"type": "string", "enum": list(EMITTERS), "default": "markdown"},
                "type": {"type": "string", "enum": ["procedural", "descriptive"], "default": "descriptive"},
            },
            "required": ["text"],
        },
    },
]


def _ok(id_, result):
    return {"jsonrpc": "2.0", "id": id_, "result": result}


def _err(id_, code, message):
    return {"jsonrpc": "2.0", "id": id_, "error": {"code": code, "message": message}}


def _handle(msg: dict):
    mid = msg.get("id")
    method = msg.get("method")
    params = msg.get("params") or {}
    if method == "initialize":
        return _ok(
            mid,
            {
                "protocolVersion": PROTOCOL,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "oneread", "version": "1.0.0"},
            },
        )
    if method == "notifications/initialized":
        return None
    if method == "tools/list":
        return _ok(mid, {"tools": TOOLS})
    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments") or {}
        text = args.get("text") or ""
        text_type = args.get("type") or "descriptive"
        try:
            if name == "oneread_lint":
                payload = lint(text, text_type)
            elif name == "oneread_compile":
                result = compile_text(text, text_type)
                payload = {k: v for k, v in result.items() if k != "ir"}
                payload["ir_lint"] = result["ir"]["lint"]
            elif name == "oneread_emit":
                target = args.get("to") or "markdown"
                compiled = compile_text(text, text_type)
                payload = {
                    "to": target,
                    "compiled": compiled["compiled"],
                    "output": emit(target, ir=compiled["ir"], text_type=text_type),
                    "after": compiled["after"],
                }
            else:
                return _err(mid, -32601, f"unknown tool {name}")
        except Exception as exc:  # noqa: BLE001
            return _ok(
                mid,
                {
                    "content": [{"type": "text", "text": f"error: {exc}"}],
                    "isError": True,
                },
            )
        return _ok(
            mid,
            {"content": [{"type": "text", "text": json.dumps(payload, indent=2)}]},
        )
    if method == "ping":
        return _ok(mid, {})
    return _err(mid, -32601, f"unknown method {method}")


def main() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(msg, dict):
            continue
        reply = _handle(msg)
        if reply is not None:
            sys.stdout.write(json.dumps(reply) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
