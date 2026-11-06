# Assignment 03 — A small tool with an honest interface

**Level:** L3 (independent) · **Weight:** 20% · **Time:** 6–8 hours

## Scenario / Problem statement

Your lab has a folder of FASTA files that arrive from different people, in different
states of repair. Someone has to answer, quickly and repeatably: *is this file usable,
and what exactly is wrong with it if not?* Bash one-liners have stopped scaling and
nobody trusts the last one anyway.

Build the small tool. It must be useful to a colleague who has never read your code,
and it must refuse to guess.

## Requirements / Task

1. **A package** `seqvet/` under `src/`, with at least three public functions:
   - `load(path)` — parse records, raising a specific exception class on malformed
     input;
   - `profile(records)` — return per-record statistics as a list of dataclass
     instances (not dicts, not printed text);
   - `verdict(records, rules=None)` — return a verdict object carrying an overall
     status (`ok` / `warn` / `fail`), a list of named findings, and the rule set used.
2. **A CLI** `seqvet` with at least two subcommands, `check` and `profile`, a `--json`
   flag on both, and exit codes `0` / `1` / `2` meaning what Module 1 says they mean.
3. **At least 15 tests**, of which:
   - 5 test success paths with hand-computed expectations;
   - 5 test failures (each raising the documented exception, not any exception);
   - 3 test exit codes through `main(argv)`;
   - 2 test that the JSON output parses and contains the documented keys.
4. **Documentation**: a README with install/run/test, plus a docstring on every public
   function containing at least one doctest that actually runs.
5. **A `DESIGN.md`, max one page**, stating: what the tool deliberately does not do,
   the two design decisions you would defend hardest, and one decision you are unsure
   about.

## Deliverables

```text
assignment-03/
├── src/seqvet/{__init__,core,cli}.py
├── tests/test_core.py
├── tests/test_cli.py
├── pyproject.toml
├── README.md
└── DESIGN.md
```

## Rubric (20 points)

| Criterion | Points | What earns full marks |
|---|---|---|
| Package structure and public API | 3 | `__init__` exports a deliberate API; internals not leaked |
| Functions return data, not print | 3 | `profile`/`verdict` return objects that tests can assert on |
| Exception design | 3 | One custom class, raised where detected, documented, not swallowed |
| CLI contract | 3 | Exit codes demonstrated; `--json` output parseable with nothing on stdout but JSON |
| Tests | 4 | 15+, the specified mix, none tautological |
| Doctests run | 1 | `pytest --doctest-modules` passes |
| DESIGN.md honesty | 3 | Names a limitation and an uncertainty; not a restatement of the README |

## Reproducibility requirement

`pip install -e . && python -m pytest -q && seqvet check <path>` must work from a
fresh clone with no edits. Include the transcript.

## Integrity and attribution

- AI assistance permitted with disclosure in `DESIGN.md`.
- If you adapt code from `seqreport`, say which lines and why. Adapting well is a
  skill; hiding it is a conduct issue. (MIT licence: attribution is required if you
  copy code.)
- No citation requirement, and no marks for citing anything.

## Extension (bonus)

Add a `--rules rules.toml` file so thresholds live in data rather than code, and
demonstrate two rule sets producing different verdicts on the same file.
