# Learning path

## The full path (25–30 hours)

| Step | What | Time | You can stop here if… |
|---|---|---|---|
| 1 | [Installation](installation.md) | 10 min | never — everything depends on it |
| 2 | [Module 1](modules/01-environment-and-jupyter.md) + [Practical 01](practicals/practical-01-setup-and-first-report.md) | 4 h | you only need to run tools others wrote |
| 3 | [Module 2](modules/02-types-control-flow-sequences.md) + [Practical 02](practicals/practical-02-composition-by-hand.md) | 5 h | you only need to count and summarise |
| 4 | [Assignment 01](assessments/assignment-01-environment-log.md), [Assignment 02](assessments/assignment-02-composition-report.md) | 8 h | you need to report numbers, not build tools |
| 5 | [Module 3](modules/03-functions-modules-errors.md) + [Practical 03](practicals/practical-03-traceback-forensics.md) + [Practical 04](practicals/practical-04-write-a-parser.md) | 7 h | — |
| 6 | [Practical 05](practicals/practical-05-reproducible-workflow.md), [Assignment 03](assessments/assignment-03-mini-tool.md) | 9 h | — |
| 7 | One [challenge](assessments/challenge-01-ambiguous-alphabets.md) | 4–8 h | — |
| 8 | [Mini-project](https://github.com/cls-open/python-for-biologists/blob/main/projects/mini_projects/README.md) | 4–6 h | you have what most people need |
| 9 | [Capstone](https://github.com/cls-open/python-for-biologists/blob/main/projects/capstone/README.md) | 20–25 h | needs Modules 4–6 (not yet written) |

## Short paths

**The weekend (8 hours).** Installation → Module 1 → Module 2 §1–§5 → Practical 02 →
Module 3 §1–§4 → Practical 03. You will be able to read, run and repair small Python
programs that handle sequence files. You will not yet be able to design one.

**The "I write scripts but nobody runs them" path.** Module 1 §4–§6 (exit codes,
determinism) → Module 3 in full → Practical 05 → Assignment 03 → Challenge 02. This is
the highest-value eight hours in the repository for anyone already writing code.

**The teaching path.** [Instructor pack](instructor/teaching-plans.md), then the
standard module plan (20 contact hours) with the quiz at session 8.

## What comes after

Modules 4–8 (specified in the [roadmap](roadmap.md), not yet written) cover large-file
parsing and pandas, plotting, testing and documentation at scale, and packaging with a
real CLI. After that, the natural next repositories in the CLS-Open sequence are:

- [bioinformatics-foundations](https://github.com/cls-open/bioinformatics-foundations)
  (#4) — the algorithms: translation, ORFs, pairwise alignment.
- [scientific-data-visualization](https://github.com/cls-open/scientific-data-visualization)
  (#5) — figures that survive review.
- [statistics-for-biological-sciences](https://github.com/cls-open/statistics-for-biological-sciences)
  (#6) — inference, honestly.

## How to know you are ready to move on

Not "I finished the modules". These three tests:

1. You can explain, without looking, why `seqreport qc` returns `1` for a file with
   defects and `2` for a file that is not FASTA.
2. You can take a script that works on your machine and make it work on someone else's
   from three commands, with byte-identical output.
3. You can find the cause of a bug from a traceback, and you know when the traceback is
   pointing at the wrong line.
