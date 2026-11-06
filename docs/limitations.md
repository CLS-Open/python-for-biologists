# Limitations

Written to be read before you trust anything here, and updated whenever a limitation
stops being true. If you find one that is missing, that is a content error — open an issue.

## Scope of the repository

1. **Three of eight modules exist.** Modules 1–3 are complete, 13-part lessons. Modules
   4–8 are specified in the [roadmap](roadmap.md) and are **not written**. There are no
   stub files pretending otherwise.
2. **`seqreport` is a teaching tool, not a production one.** It parses FASTA (not
   GenBank, not FASTQ), computes composition statistics, and runs a fixed rule set. It
   does not align, translate, search databases, or handle reads.
3. **No alignment, anywhere.** Position-by-position comparisons in the capstone brief are
   unaligned comparisons, and the brief says so; the alignment algorithms live in
   repository #4.
4. **Linear-time parsing only.** `parse_fasta` streams, but every check materialises the
   record list (`check_records` takes `list(records)` internally, because duplicate
   detection needs it). On a file with millions of records, that is a memory problem.
   Module 4 will address it; v0.1.0 admits it.

## Scientific limitations

5. **`guess_molecule_type` is a heuristic and is wrong in both directions.** A short
   protein made only of `A`/`C`/`G`/`T` residues is called a nucleotide; a nucleotide
   sequence of only `N` is called a protein. Both failures are pinned by tests so the
   behaviour cannot change silently, and the function is never allowed to make a
   decision that cannot be overridden (`--molecule`).
6. **Molecular weight is the average mass of a bare linear peptide.** No disulfide
   bonds, no N-acetyl or formyl group, no pyroglutamate, no signal-peptide cleavage, no
   post-translational modification of any kind. For a mature protein the real mass can
   differ by tens of daltons — chemistry, not a bug. Monoisotopic masses, which mass
   spectrometry actually reports, are not computed here.
7. **GC content is ambiguous by nature.** Two conventions are implemented and the caller
   must choose; no default is "correct".
8. **The QC rules are a rule set, not a review.** A clean report means "no rule fired",
   not "the data are sound". Conversely, every finding is a claim about the file that a
   human should confirm before acting.
9. **No invented values, ever.** `seqreport` never repairs a record. A residue with no
   tabulated mass is skipped (with `strict=False`) and reported separately; it is never
   given a plausible value. This is a deliberate limitation and the reasoning is in
   Challenge 02.
10. **The datasets are tiny and not representative.** 60 human proteins and 8 cytochrome
    c orthologues. Conclusions about "proteins" from these data are conclusions about
    these 68 sequences. The length distribution in Figure 1 is stratified by design.

## Educational limitations

11. **Modules assume English and an internet-connected install.** Translations do not
    exist yet; the HTML reports work offline once installed.
12. **No video, no autograder, no LMS integration.** The assessments have rubrics
    written for a human marker.
13. **The capstone cannot be completed to its own standard** without Modules 4–6 or
    equivalent prior knowledge. Its brief says so in its first paragraph rather than
    letting learners discover it in week three.
14. **Windows is only supported via WSL2.** Native Windows will mostly work and will fail
    in uninteresting ways.

## Maintenance limitations

15. **UniProt data changes.** The committed files are pinned by sha256 and the retrieval
    date is recorded; re-running `scripts/fetch_datasets.py --refetch` will produce
    different hashes and may change which records are returned. That is why CI verifies
    rather than refetches.
16. **The Biopython cross-validation is a comparison, not a proof.** Two implementations
    can share a wrong convention. It is stronger evidence than our own tests and weaker
    than a hand calculation against a published value; we do both.
17. **No deprecation policy yet.** Before v1.0.0 the API may change; the CHANGELOG will
    say so when it does.
