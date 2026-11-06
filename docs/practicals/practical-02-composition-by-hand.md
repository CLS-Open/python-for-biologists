# Practical 02 — Composition by hand, then by code, then disagree on purpose

**Module:** 2 · **Level:** L2 (guided) · **Time:** 50 min · **Dataset:** `datasets/sample/gene_family_cycs.fasta`, `datasets/sample/uniprot_human_subset.fasta`

## Aim

Compute the same three statistics (residue counts, molecular weight, GC content of
an ambiguous sequence) three ways — by hand, with plain Python, and with
`seqreport` — and locate the one place where a defensible difference exists.

## Instructions

1. **Hand calculation, no computer.** Take the first 12 residues of the human
   cytochrome c record (`sp|P99999|CYC_HUMAN`):

   ```bash
   seqreport stats datasets/sample/gene_family_cycs.fasta --json | \
     python -c "import json,sys; print(json.load(sys.stdin)['records'][0])"
   ```

   Write down by hand: the count of each residue, and the molecular weight using
   *residue mass* − *water* for each peptide bond. The residue masses are in
   `src/seqreport/composition.py` (`RESIDUE_MASSES`); water is 18.0153 Da.

2. **Plain Python, no `seqreport`.** In a file `by_hand.py`, compute the same three
   numbers using only `str` methods — `count`, slicing, a `for` loop. Do not import
   `seqreport` at all except to read the residue table, and if you can avoid that,
   avoid it.

3. **With the package.** In `by_package.py`, compute the same three numbers using
   `composition`, `molecular_weight` and `gc_content`.

4. **Compare.** Print a three-row table: statistic, by-hand value, package value,
   difference. The differences must be your *measured* differences, not a claim.

5. **Find the disagreement.** Now compute GC content for the synthetic sequence
   `GGCCNNNN` both ways:

   ```python
   from seqreport import gc_content
   print(gc_content("GGCCNNNN"))                      # ?
   print(gc_content("GGCCNNNN", denominator="all"))   # ?
   ```

   Both are correct. Explain in two sentences which denominator answers "what
   fraction of this molecule's bases are G or C" and which answers "of the bases we
   can interpret, what fraction are G or C".

6. **Look for it in real data — and in damaged data.** Compute the fraction of
   ambiguous residues (`X`, `B`, `Z`) per record in *both* the 60-protein subset
   and `qc_problems.fasta`. Report the maximum in each file, with the accession.

   Expect a result that is itself a lesson: the curated records are clean (the
   maximum is 0.000), and the damaged file has one record at 27/108 = 0.250. Records
   from a curated database are not the problem; files assembled by hand are.

## Deliverables

```text
p02/
├── by_hand.py         # plain Python, no seqreport statistics functions
├── by_package.py      # the same three numbers via seqreport
├── comparison.txt     # the three-row table with measured differences
└── answers.md         # the two-sentence denominator explanation + the ambiguity measurement
```

## Rubric (10 points)

| Criterion | Points | What earns full marks |
|---|---|---|
| Hand calculation is genuinely by hand | 2 | Residue counts and the mass arithmetic are visible in the file, not a single call |
| Plain-Python version is independent | 2 | Does not call `molecular_weight`/`composition`; states what it does use |
| Differences are measured | 2 | Differences are computed in code and pasted from the run; "0" is an acceptable answer if it is measured |
| Denominator explanation | 2 | Correctly separates "all bases" from "interpretable bases", in the learner's own words |
| Ambiguity measurement | 2 | Both maxima reported with accessions, and the clean/damaged contrast named |

## Common wrong answers (instructor note)

1. **Off-by-one in the water count.** A peptide of *n* residues has *n − 1* bonds,
   so subtract `(n-1) * 18.0153`, not `n * 18.0153`. For 12 residues the difference
   is 18 Da — small, in the right direction, and exactly the kind of error a
   mass-spec collaborator would spot instantly.
2. **"The two GC values can't both be right."** They measure different things. The
   teachable moment is that the *report* must state its denominator; a bare "GC
   content: 50%" for `GGCCNNNN` is ambiguous by a factor of two.
3. **Ambiguity counted over the whole file instead of per record.** A pooled count
   hides a single deeply ambiguous record: 27 ambiguous residues in 692 is 3.9%,
   which sounds acceptable, while the record that contains them is 25% ambiguous and
   should not be used for anything quantitative. Report per-record maxima.

## Extension

Add an ambiguity check to your `by_package.py` that flags any record over 5% `X`,
then compare your threshold to the package's default (`max_ambiguous_fraction=0.10`)
and explain which you would defend to a collaborator, and why.
