# Contributing

OneRead is a compiler. A change that cannot fail a test is not a change.

1. Run `python3 tests/test_oneread.py`.
2. Do not add the official ASD-STE100 dictionary. It is copyrighted.
3. Do not claim compliance or affiliation with ASD or STEMG.
4. Keep runtime dependencies at zero for `src/oneread/`.
5. New emitters go in `src/oneread/emit.py` and in the `EMITTERS` tuple.
6. New mechanical rules go in `src/oneread/lint.py` and `playground/linter.js`
   together. The playground is part of the product.
7. Before/after fixtures live in `fixtures/slop/` and `fixtures/compiled/`.
8. Do not add em dashes. House style and Rule 8.1 agree.

Issues and pull requests: https://github.com/zorost/oneread
