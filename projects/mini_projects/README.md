# Mini-project (4–6 hours) — Choose one

Both options use only the material in Modules 1–3 and the committed datasets. Each
produces a small, testable artefact and a one-page write-up.

---

## Option A — A quality-control gate for incoming files

**Setting.** Three colleagues send you FASTA files weekly. Two of them have never
produced a broken file; the third has, twice, and you found out months later.

**Build** a script `gate.py` that:

1. takes a directory, not a file, and processes every `*.fasta` in it;
2. applies the package checks with a rule set you document (which thresholds, why);
3. writes one HTML report per file plus a `summary.md` ranking files by worst severity;
4. exits non-zero if **any** file fails, naming them;
5. has at least six tests, including one for an empty directory and one for a file
   that is not FASTA at all.

**The interesting design question** (answer it in your write-up): should the gate
refuse a file with warnings but no errors? Argue for a position and make the tool do
exactly that.

**Deliverables:** `gate.py`, `tests/`, `rules.md`, `summary.md` produced from a run over
`datasets/sample/`, and `WRITEUP.md` (≤1 page).

---

## Option B — A composition dashboard for one protein family

**Setting.** Your group studies cytochrome c and keeps asking "how conserved is
position X?" in meetings. Everyone re-derives it by hand.

**Build** `family.py` that:

1. loads `datasets/sample/gene_family_cycs.fasta` and checks that all eight records are
   cytochrome-c-sized (100–115 aa) before doing anything else;
2. produces a per-position conservation table (this is a *counting* problem, not an
   alignment problem — state the assumption you are making by comparing positions
   without aligning, and what it would take to do it properly);
3. writes a heatmap of conservation, sorted so that the haem-binding motif is visible;
4. exports the table as CSV with a header row a spreadsheet can read;
5. has at least six tests, including one that fails if the family file gains a ninth
   record.

**The interesting design question:** comparing unaligned sequences position by position
is only defensible because these eight are the same length ±8 and the comparison is
anchored on a conserved motif. Say where the assumption breaks, and what you would do
instead.

**Deliverables:** `family.py`, `tests/`, `conservation.csv`, `heatmap.png`, `WRITEUP.md`
(≤1 page).

---

## Marking (20 points)

| Criterion | Points | Full marks |
|---|---|---|
| Works on the shipped data, numbers checked | 4 | Numbers match an independent recomputation |
| Tests | 5 | ≥6 tests, at least two of which are failure tests |
| Failure behaviour | 4 | Non-zero exit, named files, no silent skipping |
| Reproducibility | 3 | Two runs → identical artefacts; command shown |
| Write-up answers the design question | 4 | A position, argued, and implemented |

## Rules

- AI assistance permitted with one line of disclosure.
- Data attribution (UniProt, CC BY 4.0, accessed 2026-11-06) required — licence condition.
- No citation of this course is required, and no marks are awarded for citing anything.
