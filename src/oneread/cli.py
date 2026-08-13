"""oneread CLI.

  oneread lint FILE --type procedural
  oneread ir FILE --type descriptive
  oneread compile FILE --type procedural
  oneread emit FILE --to sarif,markdown,amm
  oneread self-test
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .compile import compile_text
from .emit import EMITTERS, emit
from .ir import to_ir
from .lint import format_report, lint, self_test


def _read(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    return Path(path).read_text(encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="oneread",
        description=(
            "A compiler for technical English. Type-check AI prose against "
            "ASD-STE100 Issue 9 mechanical rules, then emit it to many surfaces. "
            "Unofficial. Not affiliated with ASD."
        ),
    )
    p.add_argument(
        "command",
        choices=["lint", "ir", "compile", "emit", "self-test"],
        help="lint | ir | compile | emit | self-test",
    )
    p.add_argument("file", nargs="?", default="-", help="input file, or - for stdin")
    p.add_argument(
        "--type",
        dest="text_type",
        default="descriptive",
        choices=["procedural", "descriptive"],
    )
    p.add_argument(
        "--to",
        default="markdown",
        help=f"comma-separated emitters: {','.join(EMITTERS)}",
    )
    p.add_argument("--report", action="store_true", help="human report instead of JSON")
    p.add_argument("--out", default="", help="directory for emit (prints stdout if empty)")
    args = p.parse_args(argv)

    if args.command == "self-test":
        self_test()
        sample = compile_text("Please set up the cluster; it's ready.", "procedural")
        assert "please" not in sample["compiled"].lower()
        assert "configure" in sample["compiled"].lower()
        print("compile self-test OK")
        return 0

    text = _read(args.file)
    source = "stdin" if args.file == "-" else args.file

    if args.command == "lint":
        result = lint(text, args.text_type)
        if args.report:
            print(format_report(result))
        else:
            print(json.dumps(result, indent=2))
        return 1 if result["violations_total"] else 0

    if args.command == "ir":
        print(json.dumps(to_ir(text, args.text_type, source=source), indent=2))
        return 0

    if args.command == "compile":
        result = compile_text(text, args.text_type)
        if args.report:
            print(result["compiled"])
            print("---")
            print(
                f"before {result['before']['violations_total']} -> "
                f"after {result['after']['violations_total']}"
            )
            if result["needs_model"]:
                print("needs-model:", ", ".join(result["needs_model"]))
        else:
            slim = {k: v for k, v in result.items() if k != "ir"}
            slim["ir_lint"] = result["ir"]["lint"]
            print(json.dumps(slim, indent=2))
        return 0

    if args.command == "emit":
        targets = [t.strip() for t in args.to.split(",") if t.strip()]
        compiled = compile_text(text, args.text_type)
        ir = compiled["ir"]
        ir["findings"] = compiled["ir"].get("findings") or lint(compiled["compiled"], args.text_type)["findings"]
        out_dir = Path(args.out) if args.out else None
        if out_dir:
            out_dir.mkdir(parents=True, exist_ok=True)
        for t in targets:
            rendered = emit(t, ir=ir, text_type=args.text_type, source=source)
            ext = {
                "markdown": "md",
                "html": "html",
                "sarif": "sarif",
                "github": "txt",
                "slack": "json",
                "openapi": "json",
                "skill": "md",
                "mcp": "json",
                "rfc9457": "json",
                "amm": "txt",
            }.get(t, "txt")
            if out_dir:
                dest = out_dir / f"{t}.{ext}"
                dest.write_text(rendered, encoding="utf-8")
                print(dest)
            else:
                if len(targets) > 1:
                    print(f"----- {t} -----")
                print(rendered)
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
