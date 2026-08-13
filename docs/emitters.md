# Emitters

`python3 -m oneread.cli emit FILE --to markdown,sarif,amm --out out/`

| Target | File | Job |
|---|---|---|
| `markdown` | `.md` | README, runbook, ADR |
| `html` | `.html` | docs site, WordPress body |
| `sarif` | `.sarif` | GitHub code scanning, VS Code |
| `github` | `.txt` | workflow `::warning` annotations |
| `slack` | `.json` | Block Kit runbook |
| `openapi` | `.json` | `summary` + `description` |
| `skill` | `.md` | SKILL.md body |
| `mcp` | `.json` | tool description + inputSchema |
| `rfc9457` | `.json` | Problem Details `title` / `detail` |
| `amm` | `.txt` | aviation maintenance procedure skeleton |

The AMM emitter wraps STE steps in WARNING / CAUTION / NOTE / PROCEDURE /
RESULT. It cannot certify an AMM page. The manufacturer publication spec and
the official dictionary still govern.

MCP tool descriptions and OpenAPI summaries are the highest-leverage software
targets. An agent that cannot ask a clarifying question is the tired reader
STE was designed for.
