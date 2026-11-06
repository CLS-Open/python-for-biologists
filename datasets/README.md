# Datasets

**These are REAL data, not simulated data.** Every sequence in `sample/` was
retrieved from UniProt on **2026-11-06** and is identified by its accession in
the FASTA header. Nothing here was invented, interpolated or generated — with one
deliberate exception, clearly labelled below: `qc_problems.fasta` is real data
with *documented damage* planted in it.

| File | What it is | Records | Licence |
|---|---|---:|---|
| `sample/uniprot_human_subset.fasta` | 60 reviewed human proteins (Swiss-Prot), 100–800 aa | 60 | CC BY 4.0 — © the UniProt Consortium |
| `sample/gene_family_cycs.fasta` | Cytochrome c orthologues, one curated entry per species, 8 species | 8 | CC BY 4.0 — © the UniProt Consortium |
| `sample/qc_problems.fasta` | The cytochrome c records with **seven defects planted on purpose** | 8 | CC BY 4.0 — derived; alterations by CLS-Open |

Source: `https://rest.uniprot.org/uniprotkb/` · Query strings, retrieval date,
record counts and sha256 for every file are in `metadata/`.

## Why real data

A teaching dataset of invented sequences teaches learners to handle invented
sequences. Real records arrive with the things that actually cause trouble:

- identifiers like `sp|P99999|CYC_HUMAN`, where the "ID" is three fields glued
  together with `|` (the lessons spend time on this);
- descriptions with `OS=`, `OX=`, `GN=`, `PE=`, `SV=` — a key–value convention
  that is *almost* but not quite parseable;
- line wrapping at 60 characters that does not divide the sequence length;
- sequences with legitimate ambiguity (`X`, `B`, `Z`), selenocysteine (`U`) and
  pyrrolysine (`O`);
- records whose length is not what a textbook diagram led you to expect.

## The planted defects are not a trick

`qc_problems.fasta` contains seven defects that learners are asked to find with
code, not by eye. Each is listed in `metadata/qc_problems.yml` with the source
accession and the exact alteration (which residue, what it was, what it became).
A test (`tests/test_datasets.py`) asserts that the file contains *exactly* those
defects, so the documentation and the data cannot drift apart.

## Licensing and attribution

UniProt data are distributed under **CC BY 4.0**. If you reuse these files, keep
the attribution:

> The UniProt Consortium. UniProt Knowledgebase (UniProtKB/Swiss-Prot).
> https://www.uniprot.org. Accessed 2026-11-06. CC BY 4.0.

The subset is small and redistributable, and each record keeps its accession, so
anyone can re-fetch the original and verify that nothing was altered.

## Reproducing or refreshing

```bash
python scripts/fetch_datasets.py             # verify: file hashes vs metadata (no network)
python scripts/fetch_datasets.py --refetch   # re-download from UniProt, rewrite metadata
python scripts/make_qc_dataset.py            # rebuild the planted-defect file
```

`--refetch` is a deliberate act, not part of CI: UniProt grows, so re-fetching
later *will* change the hashes and may change the record set. CI only verifies.

## Sizes

Everything is under 20 KB in total, so cloning is instant on a slow connection.
There is deliberately no large dataset here: module 4 (streaming and
pandas) generates its own larger synthetic file with a seeded script rather than
shipping megabytes that most learners will never open. That generator is part of
the module, not of this directory — see `docs/modules/04-*.md` when it is written.
