# Representative model output

These files are labeled examples of how frontier models write technical prose
without a controlled-language gate. They are not a ranked benchmark and they
are not an attack on any vendor.

- `claude-sonnet.md` is a constructed README-shaped sample of typical model
  slop (long sentences, contraction, `-ing` clause). It is not quoted from a
  live API run.
- `gpt.md`, `gemini.md`, and `kimi.md` are constructed to show the failure
  modes those families commonly produce (hedges, synonym rotation, filler,
  trailing conditions). They are not quoted from a live API run.

Lint each file with:

    python3 -m oneread.cli lint fixtures/models/claude-sonnet.md --type descriptive --report
