---
name: oneread
version: 1.0.0
description: >
  Compile technical text with OneRead: type-check against ASD-STE100 Issue 9
  mechanical rules, lower to ORIR, emit to markdown, OpenAPI, SARIF, skills,
  MCP, Slack, RFC 9457, or aviation AMM. Use when the user says OneRead,
  ASD-STE100, Simplified Technical English, STE, or asks for docs a tired
  non-native reader cannot misread. Do not use for marketing or social posts.
license: MIT
compatibility: cursor claude-code codex gemini-cli opencode
metadata:
  standard: ASD-STE100 Issue 9 (2025-01-15)
  product: OneRead
---

# OneRead (agent adapter)

You are not a prompt that "writes simply." You are the front end of a compiler.

1. Classify the passage: procedural (20-word sentences, imperative) or descriptive (25-word sentences).
2. Run the compiler when Python is available:

```bash
python3 -m oneread.cli lint FILE --type procedural --report
python3 -m oneread.cli compile FILE --type procedural --report
python3 -m oneread.cli emit FILE --type procedural --to markdown,sarif,amm
```

3. If Python is not available, apply the mechanical rules yourself, then say so. The official wording is in the free standard at https://www.asd-ste100.org/.
4. Never touch code, identifiers, commands, quoted errors, CVE IDs, or UI labels.
5. Never claim ASD-STE100 compliance. No tool can certify it.

## Mechanical rules (Issue 9, paraphrased)

- Procedural: max 20 words, one instruction per sentence, condition before command.
- Descriptive: max 25 words, one topic per paragraph, max six sentences per paragraph.
- Verbs: infinitive, imperative, simple present, simple past, simple future. No present perfect. No -ing as a verb. Active voice.
- Modals: can, will, must. Banned: should, would, may, might, could.
- Complete grammar: no contractions, keep articles, keep "that".
- No semicolons. No em dashes. No e.g. / i.e. / etc.
- One word, one meaning, for the whole document.
- WARNING = injury. CAUTION = equipment or data damage. NOTE = information only, never a command.
- Signal word, then command or condition, then the risk.

Full catalog, IR spec, and emitters: the OneRead repository README.

This adapter is unofficial. Not affiliated with ASD or STEMG. Its job is to run the OneRead compiler, not to replace it.
