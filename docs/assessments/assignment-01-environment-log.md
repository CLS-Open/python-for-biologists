# Assignment 01 — An environment log a stranger can rebuild from

**Level:** L2 (guided) · **Weight:** 10% · **Time:** 2–3 hours

## Scenario / Problem statement

You are handing a small analysis to a collaborator in another country. They have
the data and the code, and the analysis raised a `ModuleNotFoundError` on their
machine. Your task is not to "send the right versions" — it is to produce a record
of your environment precise enough that they can rebuild it without asking you a
question.

This is the smallest, most boring deliverable in the course and the one that
decides whether the other deliverables ever run again.

## Requirements / Task

1. Produce `environment-log.md` containing, for a working install of this
   repository:
   - the operating system and its version;
   - `python --version` and the **full path** to the interpreter;
   - the output of `python -m pip list` (or `pip freeze`);
   - `seqreport --version`;
   - the path `import seqreport` resolves to, and whether it is inside the
     repository (editable) or inside `site-packages`;
   - the exit codes of three commands you ran, with the commands.
2. Produce `rebuild.sh`, a script that takes a *fresh* machine with only Python
   installed to a working install, and does so idempotently (running it twice must
   not break anything).
3. Demonstrate the rebuild works: run `rebuild.sh` in a directory that has never
   seen this project, then run `seqreport stats` on the gene-family dataset, and
   paste the transcript into `proof.txt`.
4. State in one short paragraph **what your log does not capture** (hardware?
   compiler? system libraries? a `pip` version that resolves differently next
   month?). Do not skip this part; it is the part that is marked.

## Deliverables

```text
assignment-01/
├── environment-log.md
├── rebuild.sh
└── proof.txt          # the fresh-directory transcript
```

## Rubric (10 points)

| Criterion | Points | What earns full marks |
|---|---|---|
| Every required field present and accurate | 3 | Copy-pasted from real runs, not typed from memory |
| `rebuild.sh` is idempotent | 2 | Second run succeeds; no `rm -rf` of anything the user owns |
| `rebuild.sh` fails loudly | 2 | `set -euo pipefail`; a missing prerequisite stops the script with a message |
| Proof of rebuild | 2 | Transcript from a directory that never contained the project |
| Limitations paragraph is specific | 1 | Names real gaps, not "results may vary" |

## Reproducibility requirement

A grader must be able to run, from a fresh clone of **your** submission:

```bash
bash rebuild.sh && seqreport --version && python -m pytest -q
```

and see the same versions recorded in `environment-log.md`.

## Integrity and attribution

- Using documentation, your own notes and AI assistants is permitted. If you used an
  AI assistant to write `rebuild.sh`, say so in one line — this is a disclosure
  requirement, not a penalty.
- You are **not** required to cite this course or any publication, and no marks are
  awarded for doing so.
- Copying another student's environment log produces a log that does not describe
  your machine, and the proof step will not reproduce. Do your own.

## Extension (bonus, not required)

Add a `requirements.txt` with exact `==` pins produced by `pip freeze`, and write two
sentences on why pinning everything is neither necessary nor sufficient for
reproducibility.
