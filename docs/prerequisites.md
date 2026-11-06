# Prerequisites

## You need

- **Curiosity about biology.** The examples are proteins and sequences; nothing is
  assumed beyond "DNA encodes protein" and "sequences are written as strings of
  letters".
- **Comfort with files and folders** — creating, moving, and knowing where a file is.
  If a terminal is completely new, spend 30 minutes on any basic bash tutorial first;
  the [linux-git-for-bioinformatics](https://github.com/cls-open/linux-git-for-bioinformatics)
  repository is this initiative's course for exactly that.
- **A computer you can install software on.** No GPU. No paid service. No internet
  access is needed after the install.
- **Time.** Modules 1–3 plus the practicals is about 25–30 hours of real work for a
  beginner. The five-minute tour in the README is not that.

## You do **not** need

- Prior programming experience. This is the beginner entry point of the fifteen-repository
  sequence; Module 1 starts at the environment.
- A statistics background. Module 2 needs arithmetic, not inference.
- Molecular biology beyond the basics. Where biology matters (what a residue is, what
  conservation implies), the module says so explicitly.
- Biopython, pandas, numpy, matplotlib or an IDE. Modules 1–3 use plain Python.

## Self-check: are you in the right course?

| Statement | If yes |
|---|---|
| "I have never written a program." | Start at [Module 1](modules/01-environment-and-jupyter.md). This is the right course. |
| "I write scripts but nobody else has ever run them." | Skim Module 1, read Modules 2–3 carefully, do Practical 05 and Assignment 03. |
| "I have used Python, mostly by copying from Stack Overflow." | Do the two challenges (`assessments/challenge-01-ambiguous-alphabets.md`, `challenge-02-fail-loudly.md`); they are designed for you. |
| "I want to learn alignment and translation algorithms." | You want [bioinformatics-foundations](https://github.com/cls-open/bioinformatics-foundations) (repository #4). |
| "I want to analyse a genome in an afternoon." | You want the intermediate repositories (genomics and NGS analysis). This one deliberately starts smaller. |

## Known environment constraints

- **Windows native**: use WSL2. The materials assume a POSIX shell in a handful of
  places and the failure modes on native Windows are not worth teaching around.
- **Python 3.9 or older**: `requires-python = ">=3.10"`. The code uses modern typing
  syntax; it will not run on 3.9 and pretending otherwise would waste your time.
- **No internet**: everything works offline **after** the install, including the HTML
  reports (no external assets, no web fonts, no CDN).
