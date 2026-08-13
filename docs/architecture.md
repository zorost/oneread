# Architecture

OneRead is a four-stage pipeline. The skill is stage zero. It is optional.

```
prose  ->  parse  ->  type-check  ->  ORIR  ->  emit
                \                       |
                 \                      +-- markdown
                  \                     +-- html
                   mechanical compile   +-- sarif
                   (subset of rules)    +-- github annotations
                                        +-- slack Block Kit
                                        +-- openapi summary/description
                                        +-- SKILL.md
                                        +-- MCP tool description
                                        +-- RFC 9457 problem details
                                        +-- aviation AMM skeleton
```

## Stages

1. **Parse.** Split passages. Classify each as procedural, descriptive, mixed,
   or protected (code fences, headings). Count words with Rule 8.6: identifiers,
   numbers with units, and quoted commands count as one word.
2. **Type-check.** `oneread.lint` runs mechanical rules. It is a regex, not a
   grammar parser. It undercounts. Numbers are comparable between two texts
   run through the same version. They are not a compliance verdict.
3. **Compile.** `oneread.compile` rewrites the subset a program can prove:
   contractions, Latin abbreviations, courtesy filler, wordy phrases,
   semicolons, em dashes, `make sure` without `that`, a few phrasal verbs.
   Residual keys (`sentence_over_limit`, `banned_modal`, `ing_clause`,
   `trailing_condition`, `synonym_rotation`) are marked `needs_model`.
4. **Emit.** Every backend reads ORIR. None of them re-parse prose.

Protected tokens never move: code spans, fences, URLs, identifiers.

## What this is not

It is not the official dictionary. The dictionary is copyrighted by ASD and is
not reproduced here. Full vocabulary compliance requires Issue 9.

It is not a replacement for HyperSTE, Congree, or Acrolinx. Those are
authoring checkers, often licensed, sitting in a writer's editor. OneRead sits
in the agent and CI path, where those tools are not.

It is not another agent skill. Skills that tell a model to write in STE
already exist. A skill is a prompt. The next call drifts. CI cannot fail a
prompt. This repo keeps a skill adapter whose job is to run the compiler, and
adds the IR a prompt cannot be.
