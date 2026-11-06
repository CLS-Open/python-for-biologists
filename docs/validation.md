# Validation — what has actually been checked

Every claim on this page was produced by running the command shown. Nothing here is
"should work". If a number is stale, that is a bug: the commands are in CI.

## 1. Independent cross-validation (Biopython 1.88)

```bash
python scripts/validate_against_biopython.py
```

| Comparison | Result |
|---|---|
| Record parsing: identifier and sequence of every committed record | **76/76 agreed** |
| Molecular weight, all records with standard residues | **75/75 agreed** within 1e-6 Da |
| GC content, 200 seeded pseudo-random DNA sequences | **200/200 agreed** to 1e-12 |
| Refusal on unresolvable residues (`X`, `*`, `1`, `-`) | **4/4 agreed** — both refuse |
| Documented divergence: empty sequence | Biopython returns 18.0153 Da; we refuse. **Checked in the direction claimed**, not ignored |

Total: **356 comparisons**, all agreeing except the one documented divergence. Agreement
with a second implementation is evidence, not proof: both could share a wrong
convention. That is why section 2 exists.

## 2. Hand-computed expectations in the test suite

```bash
python -m pytest -q          # 230 passed
```

The tests do not ask the code what the answer is. Examples of hand-derived values that
are asserted:

| Claim | Hand computation | Test |
|---|---|---|
| `molecular_weight("MA")` = 220.2892 Da | 149.2113 + 89.0932 − 18.0153 | `test_composition.py::test_specific_peptide` |
| `molecular_weight("AA")` = 160.1711 Da | 2 × 89.0932 − 18.0153 | `test_dipeptide_loses_one_water` |
| `gc_content("GGGCCCATA")` = 0.667 | 6 G/C ÷ 9 unambiguous | `test_hand_computed` |
| `gc_skew("GGGGCC")` = 1/3 | (4 − 2) / (4 + 2) | `test_gc_skew_hand_computed` |
| `kmer_counts("ACGTAC", 2)` has `AC: 2` | overlapping 2-mers: AC, CG, GT, TA, AC | `test_counts_overlap` |
| Human cytochrome c mass = 11,748.6 Da | package, Biopython and a hand sum all agree | `test_cli.py::test_stats_table_on_gene_family` |

Suite composition (230 tests):

| Area | Tests | What they pin down |
|---|---|---|
| Parsing | 36 | multi-line, gzip, blank lines, CRLF, raw vs normalised sequence, four error paths |
| Composition | 60 | every statistic, both GC denominators, undefined cases, mass table sanity |
| Quality checks | 28 | every issue code, severities, thresholds, file-level vs record-level |
| Reporting | 32 | three renderings agree; HTML has no external resources; IDs are escaped |
| CLI | 21 | real argv, exit codes 0/1/2, JSON schema, gzip input, format inference |
| CLI in-process | 22 | the paths a subprocess cannot reach cheaply |
| Dataset integrity | 31 | recorded sha256s, record counts, planted defects match their documentation, no invented data |

In addition, 13 **doctests** in the package docstrings are executed separately
(`pytest --doctest-modules src/seqreport`), and they are run under four different
`PYTHONHASHSEED` values, because one of them was originally written so that its expected
output depended on set iteration order. It failed exactly as Module 1 §4 says it should.

Line coverage of `src/seqreport` is **99%** (552 statements, 4 missed; the misses are
defensive branches named in the CI coverage report). Coverage is reported because it is
measurable, not because it is proof of correctness.

## 3. Data integrity

```bash
python scripts/fetch_datasets.py        # verifies sha256 of every committed file
python scripts/make_qc_dataset.py       # regenerates the planted-defect file deterministically
```

- Every dataset has a metadata YAML recording source, query, retrieval date, licence,
  record count, byte size and sha256.
- The files are **real UniProt records** (`synthetic: false`), retrieved 2026-11-06 under
  CC BY 4.0; attribution is in the metadata and in `datasets/README.md`.
- `qc_problems.fasta` contains seven defects planted on purpose. A test asserts that the
  file contains *exactly* those defects, so the documentation and the data cannot drift.

## 4. Reproducibility of the figures

```bash
python scripts/make_figures.py
for s in 1 2 3; do PYTHONHASHSEED=$s python scripts/make_figures.py; md5sum figures/*.png | md5sum; done
```

All four figures are byte-identical across `PYTHONHASHSEED` values 1, 2 and 3 (verified
2026-11-06). CI re-runs the generator and fails if the committed PNGs change.

## 5. Notebooks execute

```bash
jupyter nbconvert --to notebook --execute --stdout notebooks/01_quality_control.ipynb
```

12 code cells, 0 errors, executed from the repository root and from `/tmp` (the notebook
locates the repository by walking up to `pyproject.toml`, never by assuming a working
directory). CI executes every notebook on every push.

## 6. References

```bash
python scripts/check_references.py
```

Every DOI cited in the documentation resolves through the Crossref API **and** its title
matches the claim made about it. Verified 2026-11-06. Fabricated citations are the failure
mode this check exists to make impossible.

## 7. Documentation and links

```bash
python scripts/check_docs_links.py      # internal links and anchors
mkdocs build --strict                   # zero warnings
```

## What is **not** validated

- **Biological correctness of the capstone's interpretation.** Conservation across eight
  sequences says nothing about function; the capstone says so.
- **Performance.** No benchmarks are claimed. The parser is O(L) and the checks are
  O(n·L), which is asserted by inspection, not measured at scale.
- **Platform coverage.** CI runs Linux on Python 3.10–3.12. macOS and WSL2 are expected to
  work; native Windows is not claimed.
