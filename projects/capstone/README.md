# Capstone — Characterise a gene family across eight species

**Level:** L4 · **Time:** 20–25 hours · **Weight:** 30% (if used as the course's final assessment)

> **Status note, stated up front:** the full form of this capstone needs Modules 4–6
> (streaming and large-file parsing, pandas, plotting). Those modules are **specified
> but not yet written** in v0.1.0 (see [`docs/roadmap.md`](../../docs/roadmap.md)).
> The capstone is therefore specified here and cannot be completed to the standard
> below until those modules exist, or unless the learner already has that background.
> We would rather say this than hand out a brief nobody can finish.

## The scientific question

Cytochrome c is one of the most conserved respiratory proteins known: the human and
yeast proteins are both ~105–109 residues and share the Cys-X-X-Cys-His haem-binding
motif. Two questions follow, and they are the capstone:

1. **How conserved is it, really, and where is it conserved?** Report conservation per
   position across the eight species in `datasets/sample/gene_family_cycs.fasta`, and
   say which positions are invariant.
2. **Do the invariant positions correspond to the ones that matter mechanistically?**
   The haem-binding motif and the lysine-rich surface that docks cytochrome c to its
   partners are the two features to check. State your evidence and its limits.

The second question cannot be *answered* from sequence alone. That is the point.

## What you must produce

```text
capstone/
├── analysis/
│   ├── qc.py               # validate the input before analysing it
│   ├── conservation.py     # per-position conservation, with the method stated
│   ├── report.py           # renders report.html + report.json
│   └── figures.py          # every figure, regenerated from data
├── tests/                  # ≥12 tests, including failure paths
├── data/                   # inputs (symlink or copied from datasets/), with hashes
├── outputs/
│   ├── report.html         # self-contained, opens offline
│   ├── report.json
│   ├── conservation.csv
│   └── figure1.png, figure2.png
├── METHOD.md               # ≤2 pages: what you did, and the assumptions
├── LIMITATIONS.md          # ≤1 page: what this cannot tell you
└── README.md               # exactly three commands: install, run, test
```

## Requirements, in order of importance

1. **Validate before you analyse.** A QC step that refuses the input if it is not
   eight cytochrome-c-sized records. A capstone that runs happily on a half-downloaded
   file is a failed capstone.
2. **State the alignment assumption.** Position-by-position comparison of unaligned
   sequences is only defensible if you say so and justify it. If you align them
   (allowed, with Biopython), say which algorithm, which scoring, which gap penalties,
   and show that a different penalty does not change your conclusions.
3. **Every number traceable.** Each claim in `METHOD.md` must be reproducible by
   running one command. No number typed from memory.
4. **Two artefacts for two audiences:** a self-contained HTML report for a
   collaborator, and JSON/CSV for whoever comes next.
5. **Figures with units, captions and one honest panel.** At least one panel must show
   something that does *not* support your main claim — for example where the method
   gives no answer, or where a position is conserved but uninterpretable.
6. **The limitations section is marked, not decorative.** Name at least four specific
   things the analysis cannot establish (orthology by annotation rather than
   phylogeny; conservation ≠ function; eight species is not a phylogeny; unaligned
   positions; no structural data).

## Rubric (100 points)

| Criterion | Points | Full marks |
|---|---|---|
| QC step, with tests | 10 | Refuses wrong-sized or malformed input; names the reason |
| Conservation method correct and stated | 15 | Denominator, treatment of gaps/ambiguity, and the unaligned caveat all explicit |
| Numbers traceable | 15 | Every claim reproducible by one documented command |
| Invariant positions identified correctly | 10 | Matches an independent recomputation; includes the Cys-X-X-Cys-His motif |
| Mechanistic interpretation | 10 | Separates what the sequence shows from what it suggests; cites evidence, or says there is none |
| Figures | 10 | Units, captions, colour-blind-safe, one honest panel |
| Tests | 10 | ≥12, mixed success/failure, none tautological |
| Reproducibility | 10 | Fresh clone + three commands → identical artefacts (hashes shown) |
| Limitations and method documents | 10 | Specific, not generic; at least four real limitations |

## Reproducibility requirement

A grader runs, from a fresh clone:

```bash
pip install -e .
python -m pytest -q
python analysis/report.py --out outputs/
```

and gets byte-identical `outputs/` to the submitted ones, with the hashes to prove it.

## Integrity and attribution

- **AI assistance:** permitted, with disclosure of which parts. You must be able to
  explain every line you submit.
- **Data attribution:** UniProt, CC BY 4.0, accessed 2026-11-06 — required, because it
  is a licence condition. This is the *only* citation obligation.
- **No citation of this course** is required or rewarded. Do not add backlinks, and do
  not cite publications you have not read: a fabricated reference is worse than none.
- **Fabricated results** end the assessment regardless of the rest of the submission.
