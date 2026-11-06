# Python Foundations for the Life Sciences — CLS-Open #1

**CLS-Open repository 1 of 15** · Level: **beginner** · Status: **v0.1.0 (honest launch standard: Modules 1–3 complete, Modules 4–8 specified)**

> Learn Python by doing something that matters: read real protein records, compute what they actually contain, find the defects that real files really have, and produce a report someone else can re-run.

## What you get in v0.1.0

| Component | Status |
|---|---|
| **Module 1** — Your environment, your evidence | ✅ complete (13-part lesson) |
| **Module 2** — Types, control flow and the shape of a sequence | ✅ complete (13-part lesson) |
| **Module 3** — Functions, modules and the discipline of failing well | ✅ complete (13-part lesson) |
| **`seqreport`** — FASTA parsing, composition, QC, HTML/Markdown/JSON reports | ✅ working, **230 tests, 99% line coverage**, cross-validated against Biopython |
| Executed notebook (`01_quality_control.ipynb`) | ✅ 12 code cells, outputs stored, re-executed by CI |
| 5 guided practicals with rubrics | ✅ complete |
| 3 assignments, 2 challenges, quiz with answer key | ✅ complete |
| Instructor pack, mini-project, capstone specification | ✅ complete |
| Modules 4–8 (large-file parsing and pandas, plotting, testing and docs, packaging and CLI) | 🗺️ specified, not yet written — see [`docs/roadmap.md`](docs/roadmap.md) |

If a module is not in the table above, it is not in this repository yet: no placeholder
files, no empty lesson bodies. What exists is tested; what does not exist is labelled
not yet written.

## Install

```bash
git clone https://github.com/cls-open/python-for-biologists.git
cd python-for-biologists
python3 -m venv .venv && source .venv/bin/activate    # Windows: use WSL2
python -m pip install -e ".[dev]"
seqreport --version        # seqreport 0.1.0
python -m pytest -q        # expect: 230 passed
```

`seqreport` has **zero runtime dependencies** — standard library only — so you can read
every line of the thing you are learning to write.

## Run in five minutes

```bash
seqreport stats datasets/sample/gene_family_cycs.fasta          # composition table
seqreport qc datasets/sample/qc_problems.fasta                  # finds 7 planted defects, exits 1
seqreport report datasets/sample/qc_problems.fasta --out r.html  # self-contained report
seqreport windows datasets/sample/gene_family_cycs.fasta \
    --record 'sp|P99999|CYC_HUMAN' --window 21 --json            # windowed GC
jupyter lab notebooks/01_quality_control.ipynb                   # executed walkthrough
python scripts/make_figures.py                                   # regenerate the figures
```

## The data are real

All sequences come from **UniProt** (retrieved 2026-11-06, CC BY 4.0), with accession,
query, retrieval date and sha256 recorded in [`datasets/metadata/`](datasets/metadata).
Nothing is invented. One file — `qc_problems.fasta` — is real data with **seven defects
planted on purpose**, each documented with its source accession and the exact
alteration, so that the quality-control code has something true to find. See
[`datasets/README.md`](datasets/README.md).

## Exit codes mean something

| Code | Meaning |
|---|---|
| `0` | ran; no errors found |
| `1` | ran; the data **has errors** (the report names them) |
| `2` | could not run: missing file, malformed FASTA, bad argument |

CI gates on these, and Module 1 teaches them as the tool's interface.

## What this repository deliberately is not

- **Not an algorithms course.** Translation, ORFs, Needleman–Wunsch and Smith–Waterman
  live in [`bioinformatics-foundations`](https://github.com/cls-open/bioinformatics-foundations)
  (repository #4). Here Python is the subject and biology is the context.
- **Not a pandas/numpy course.** Modules 4–6 will introduce those; Modules 1–3 use plain
  Python so the data structures stay visible.
- **Not a scaffold.** There are no empty chapter directories and no "coming soon"
  lessons. Twice as much honest material beats thirty empty headings.

## Repository layout

```text
src/seqreport/     package: records, composition, qc, report, cli   (MIT)
tests/             230 tests: hand-computed expectations, properties, CLI, data integrity
docs/              lessons, practicals, assessments, instructor pack (CC BY 4.0)
notebooks/         executed walkthrough (re-executed by CI)
datasets/          real UniProt data + metadata with hashes         (CC BY 4.0)
figures/           regenerated from data by scripts/make_figures.py
scripts/           fetch, verify, validate against Biopython, build figures, check links
projects/          mini-project and capstone specifications
```

## Licence

Content CC BY 4.0 · code MIT. See [`LICENSES/README.md`](LICENSES/README.md). Data are
UniProt's, redistributed under CC BY 4.0 with attribution — see
[`datasets/README.md`](datasets/README.md).

## Contributing

Content errors, broken commands, reproducibility failures and adoption reports are the
contributions we most want. Read [`CONTRIBUTING.md`](CONTRIBUTING.md) first: it states
the standards every pull request must meet, including that notebooks must execute and
that every scientific claim needs a reference that resolves.
