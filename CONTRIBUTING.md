# Contributing

Thank you for considering a contribution. This repository is part of the CLS-Open
initiative: 15 interlinked open courses across the computational life sciences, aimed at
learners who cannot afford to pay for them.

## The contributions we most want

| Priority | Contribution | How |
|---|---|---|
| 1 | **Scientific or factual errors** | Open a "Content error" issue quoting the file and line |
| 2 | **Broken commands / non-reproducible examples** | Issue or PR — CI executes every example, so a failure is a genuine bug |
| 3 | **Accessibility problems** (colour, contrast, screen readers, bandwidth) | Issue labelled `accessibility` |
| 4 | **Adoption reports** ("I taught this to N students; here is what broke") | Issue labelled `adoption` |
| 5 | New lessons, practicals, translations | Discuss in an issue *before* writing; see below |

## Before you write a lesson

Open an issue titled `proposal: <module/lesson title>` containing:

1. the learning objective(s), stated as measurable outcomes;
2. what already exists (with links) and why it is insufficient — this project is not
   allowed to duplicate good existing material;
3. the dataset, with licence and accession;
4. how a learner can verify their own answer.

You will get a scope decision. This prevents the most common waste in open courseware:
two people writing the same mediocre lesson.

## Standards every PR must meet

- `python -m pytest -q` passes (230 tests at v0.1.0); new code has tests with
  hand-computed expectations where arithmetic is involved.
- Notebooks execute from a clean kernel: `jupyter nbconvert --execute`.
- Figures regenerate: `python scripts/make_figures.py` must leave `git diff` clean, and
  must produce identical bytes across `PYTHONHASHSEED` values.
- New datasets: under 5 MB shipped, with `datasets/metadata/<name>.yml` (source, licence,
  retrieval date, sha256, record count) and a reproducible fetch or generator script.
  **Real third-party data must name its licence and attribution**; that is a legal
  condition, not a courtesy.
- Claims are cited: every scientific statement that is not common knowledge has a
  reference that resolves via Crossref, added to `docs/references.md`. The CI check
  verifies that the DOI resolves *and* that its title matches the claim.
- No fabricated data, text, or references. Ever. This will be caught and it ends the
  contribution.
- Synthetic data is labelled synthetic in the file *and* in every figure that uses it.
- Commit messages: imperative mood, one logical change.

## What we will not accept

- Empty scaffolds: a module file with headings and no content, a "coming soon" section, a
  dataset placeholder. If it is not ready, it is not merged. The roadmap is where future
  work is described.
- Removed limitations. If you make the material less honest to make it look more
  complete, the PR is closed.
- Required citation or backlink to this project. Learners must never be asked to cite us
  as a condition of participation.

## Review process

1. CI must be green (tests, notebook execution, figure determinism, data metadata, links,
   references).
2. One maintainer review, with a checklist that includes *scientific accuracy*.
3. If a claim is contested, the standard is: show the calculation, the reference, or the
   measurement. Not seniority.

## Licence of contributions

By contributing you agree that code is licensed MIT and prose is licensed CC BY 4.0, as
described in [`LICENSES/README.md`](LICENSES/README.md). You keep your copyright; you grant
everyone else the same freedoms this material already has.

## Reporting conduct problems

See [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md). Do not open a public issue for a conduct
report.
