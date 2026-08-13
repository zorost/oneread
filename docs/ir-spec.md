# ORIR 1.0

OneRead Intermediate Representation is JSON. Schema: `schema/orir.schema.json`.

A document is a list of passages. A passage is procedural, descriptive, mixed,
or protected. A sentence carries its STE word count, its kind, and the
protected tokens inside it. Findings from the linter hang off the document,
not off a second parse.

```json
{
  "orir": "1.0",
  "source": "runbook.md",
  "default_type": "procedural",
  "passages": [
    {
      "id": "p1",
      "kind": "procedural",
      "sentences": [
        {
          "text": "If the build fails, read the log.",
          "kind": "procedural",
          "words": 7,
          "limit": 20,
          "protected": []
        }
      ]
    }
  ],
  "lint": { "violations_total": 0 },
  "findings": [],
  "disclaimer": "No tool can guarantee ASD-STE100 compliance."
}
```

Emitters must:

- leave `protected` tokens exact
- treat procedural passages as ordered steps when they emit lists
- copy the disclaimer to any human-readable surface
- refuse to claim certification

Build an IR:

```bash
python3 -m oneread.cli ir runbook.md --type procedural > runbook.orir.json
```
