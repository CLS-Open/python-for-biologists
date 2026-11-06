# Instructor materials

Start with **[teaching plans](teaching-plans.md)** — it contains the three delivery
plans, the session-by-session schedule, marking guidance and the integrity policy.

## What is here

| File | Use it for |
|---|---|
| [`teaching-plans.md`](teaching-plans.md) | Planning a course, marking, integrity, accessibility |
| [`../assessments/`](../assessments/quiz-01-modules-1-3.md) | The quiz and its answer key |
| [`../practicals/`](../practicals/practical-01-setup-and-first-report.md) | Guided sessions with rubrics |
| [`projects/mini_projects/README.md`](https://github.com/cls-open/python-for-biologists/blob/main/projects/mini_projects/README.md) | 4–6 hour project |
| [`projects/capstone/README.md`](https://github.com/cls-open/python-for-biologists/blob/main/projects/capstone/README.md) | Full capstone spec (needs Modules 4–6 for its full form) |

## Frequently asked questions from instructors

**Do learners need to install anything paid?** No. Python, the package and the data are
all free; the repository is ~35 KB of data and the only network use is the initial
install.

**Can I teach this without the later modules?** Yes — Modules 1–3 plus the practicals
form a coherent 8–20 hour course. Be explicit with learners that Modules 4–8 are
specified but not written; the roadmap says what they will contain.

**Is this the same material as `bioinformatics-foundations` (repository #4)?** No, and
the split is deliberate. Here, Python is the subject and biology is the context: types,
functions, errors, tests, packaging. Repository #4 is where the algorithms live
(translation, ORFs, Needleman–Wunsch, Smith–Waterman) with the biology as the subject.
`seqforge` (in #4) has a deliberate gap — it does not parse quality scores or report
QC — because that is this repository's `seqreport`.

**How do I handle a learner who has used Python before?** Point them at the two
challenges (`challenge-01-ambiguous-alphabets`, `challenge-02-fail-loudly`). Both are
designed to be hard for someone who is fluent in syntax but has not yet designed an
interface.

**What do I do when the material is wrong?** Open an issue with the file and line.
Content errors are the highest-priority contribution in `CONTRIBUTING.md`.
