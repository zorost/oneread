# Quickstart example

```bash
python3 -m oneread.cli lint examples/bad-readme.md --type descriptive --report
python3 -m oneread.cli compile examples/bad-readme.md --type descriptive --report
python3 -m oneread.cli emit examples/bad-readme.md --to openapi,sarif --out /tmp/oneread-out
```
