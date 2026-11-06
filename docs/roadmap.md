# Roadmap

This roadmap is written in the same spirit as the rest of the repository: it says what
exists, what does not, and what the difference costs you.

## v0.1.0 — shipped 2026-11-06

- Modules 1–3 as complete 13-part lessons.
- `seqreport` 0.1.0: FASTA parsing, composition, QC, three report renderings, five
  subcommands, 230 tests, 99% line coverage, cross-validated against Biopython.
- Five guided practicals, three assignments, two challenges, quiz with answer key,
  instructor pack, mini-project and capstone specifications.
- Real UniProt data with recorded provenance and hashes; four figures regenerated from
  data; one executed notebook.

## v0.2.0 — the next planned increment

| Item | Why it is next | Acceptance criteria |
|---|---|---|
| **Module 4 — files, formats and scale** | The parser already streams; learners need to see why that matters | GenBank and FASTQ reading demonstrated; a 200 MB synthetic file profiled for time and memory; the O(1)-vs-O(L) memory claim *measured* |
| **Module 5 — pandas for experimental tables** | The single most requested skill in this audience | A plate-reader-style CSV, groupby summaries, joins, and an honest section on what pandas hides |
| **Notebook 02** | Module 4 has no executable companion yet | Executed in CI with stored outputs |
| **`seqreport verify` subcommand** | Turns `scripts/fetch_datasets.py` into a user-facing tool | Verifies any file against a metadata YAML; tested |

## v0.3.0 — planned, not scheduled

- **Module 6 — plotting first contact** (matplotlib, then one figure-integrity exercise).
- **Module 7 — testing and documentation** (pytest fixtures, coverage, doctests, why a
  green suite is not correctness).
- **Module 8 — packaging and a real CLI** (entry points, `argparse` design, building a
  wheel, when containers are worth it).
- **Second notebook** covering QC on a larger file.

## Known gaps that are *not* on the roadmap

- **Video lectures.** Not planned. Text and executable notebooks are the medium.
- **An autograder.** The rubrics are written for human markers; automating them would
  require narrowing the tasks until they stopped being interesting.
- **Translation into other languages.** Welcome as contributions (CC BY 4.0 permits it);
  not something we can promise.
- **GenBank/FASTQ in `seqreport`.** Module 4 teaches reading them; adding them to the
  package is a v0.2 decision, not a promise.

## How to influence this

Open an issue with the `module-proposal` template. Proposals that state (a) the learning
objective, (b) what already exists and why it is insufficient, and (c) how a learner can
verify their own answer, get a scope decision rather than silence.
