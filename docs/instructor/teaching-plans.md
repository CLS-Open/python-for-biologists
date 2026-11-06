# Instructor pack — Python Foundations for the Life Sciences

This pack assumes you are teaching 10–40 learners, in a computer lab or on their own
laptops, with 10–20 contact hours available. It states what to run, what to watch for,
and where the material will fight you.

## 1. What this repository is, honestly

- **Complete in v0.1.0:** Modules 1–3 (13-part lessons), five guided practicals, three
  assignments, two challenges, a quiz with an answer key, a mini-project and a capstone
  specification, and a working, tested teaching package (`seqreport`, 230 tests).
- **Specified, not written:** Modules 4–8 (files and FASTA/GenBank at scale, pandas,
  plotting, testing and documentation, packaging and CLI). See
  [`docs/roadmap.md`](../roadmap.md). They are described in enough detail to plan
  around; they are not in the repository yet.
- **Prerequisites:** none, beyond comfort with files and folders. This is the beginner
  entry point of the fifteen-repository CLS-Open sequence.

## 2. Three delivery plans

| Plan | Contact hours | Cover | Skip | Assessment |
|---|---|---|---|---|
| **Short course** (2 days) | 8 | M1 + M2, practicals 1–2, quiz | M3, challenges | Assignment 01 + quiz |
| **Standard module** (1 semester, 20 h) | 20 | M1–M3, practicals 1–5 | Challenge 02 (offer as extension) | Assignments 01–03 + one challenge |
| **Bootcamp** (1 week intensive) | 25–30 | M1–M3 + mini-project | Formal capstone | Assignments 01–02 + mini-project + presentation |

The capstone as specified (characterise a gene family across eight species, produce a
reproducible report with tests) needs Modules 4–6 for its full form. Until those
modules exist, run the mini-project instead and say so plainly to learners.

## 3. Session-by-session plan (standard module)

| Session | Content | In-class activity | Homework |
|---|---|---|---|
| 1 (2 h) | M1 §1–§5 | Build the environment together; deliberately break it | Practical 01 |
| 2 (2 h) | M1 §6–§13 | Exit codes: three files, three codes, predict then run | Assignment 01 |
| 3 (2 h) | M2 §1–§4 | Counting and slicing at the REPL, in pairs | — |
| 4 (2 h) | M2 §5–§13 | Practical 02 (hand calculation first, computers second) | Assignment 02 |
| 5 (2 h) | M3 §1–§4 | Traceback forensics, practical 03 bugs 1–3 | — |
| 6 (2 h) | M3 §5–§13 | Practical 03 bugs 4–5; practical 04 | Assignment 03 |
| 7 (2 h) | Practical 05 | Fresh-clone test in class; watch it fail | Challenge (one of two) |
| 8 (2 h) | Review + quiz | Quiz closed-book, then live marking | Mini-project |
| 9–10 (4 h) | Mini-project | Studio format: circulate, do not lecture | Submission |

## 4. The three things that go wrong every time

1. **Environment drift.** Someone arrives with `conda` active, someone with Python
   3.9, someone on native Windows. Session 1 is where you fix this, not session 3. Have
   WSL2 instructions ready and a fallback: a browser-based environment with the
   repository pre-installed. If a learner's `seqreport --version` fails, they do not
   proceed until it prints `0.1.0`.
2. **Notebook state.** "It worked when I clicked through it." Force **Kernel → Restart
   & Run All** at the start of every session. It takes 20 seconds and prevents the most
   common false success in the course.
3. **The GC denominator argument.** It will happen. Do not resolve it by authority —
   make learners compute both numbers on `GGCCNNNN` and let the factor-of-two do the
   arguing.

## 5. Marking guidance

- **Rubrics are additive and already written** in each practical and assignment.
  Marks are for evidence, not effort.
- **Fabricated numbers are a zero** on that artefact, and the conversation afterwards
  matters more than the mark. The distinction to teach: a wrong number you measured is
  a mistake; a wrong number you invented is a different category of act.
- **Reproducibility marks are binary.** Either a fresh clone reproduces the artefacts
  or it does not. There is no partial credit for "it worked on my machine".
- **Do not award marks for citations** and do not require them. Data-provenance
  attribution (UniProt, CC BY 4.0) is required because it is a licence condition, and
  that reason should be stated to learners as such.

## 6. Academic integrity and AI assistance

The policy this material is written for, which you should adapt to your institution:

- **Permitted with disclosure** for all assignments and challenges: AI assistants,
  forums, textbooks, each other's *ideas*.
- **Not permitted:** submitting generated code you cannot explain line by line. The
  practical test is that the learner can answer "what happens if this input is empty?"
  about their own submission.
- **Required disclosure:** one line in the submission naming which tools were used for
  which parts. No penalty for disclosure.
- The repository's own `CONTRIBUTING.md` applies if learners contribute fixes upstream.

## 7. Accessibility and inclusion

- All figures use colour-blind-safe palettes and are legible at 50% width; every figure
  has a text caption carrying the numbers, so no finding depends on seeing colour.
- No material requires a paid service, a GPU, or a fast connection. The datasets total
  under 35 KB; the only network access needed is the initial install.
- The HTML reports use system fonts with no external assets, so they render offline and
  on low-bandwidth connections.
- If a learner cannot install locally, the browser-based fallback in §4 covers the
  whole course except practical 01's environment evidence, which can be replaced with a
  screenshot of `pip list` from the hosted environment.

## 8. Feedback loop

Adoption reports are the most valuable thing you can send back: how many learners, what
broke, what you had to explain twice. Open an issue labelled `adoption` (templates are in
`.github/ISSUE_TEMPLATE/`). If a session goes badly because of a defect here, that is a
bug in the material and it will be fixed.
