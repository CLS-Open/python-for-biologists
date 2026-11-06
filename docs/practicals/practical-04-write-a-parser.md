# Practical 04 — Write a FASTA parser, then try to break it

**Module:** 3 (with Module 2) · **Level:** L2 → L3 · **Time:** 75 min · **Dataset:** all three files in `datasets/sample/`

## Aim

Implement a FASTA reader in under 30 lines, feed it the dataset that contains
deliberate damage, and compare its behaviour with `seqreport`'s — including where
yours is *worse*.

## Instructions

1. **Write `my_fasta.py`** with two functions:

   ```python
   def parse(path):
       """Yield (header, sequence) tuples. Sequence is upper-cased, no whitespace."""

   def to_dict(path):
       """Return {header_id: sequence}. Decide what to do about duplicates and justify it."""
   ```

   Rules you must follow:
   - the sequence may be split over any number of lines;
   - blank lines may appear anywhere;
   - blank line handling must *not* drop a record;
   - lower case must be upper-cased in the returned sequence;
   - nothing may be read into memory twice (stream the file).

2. **Run it on the clean data.** All three files must parse without exception,
   and the record counts must match:

   ```bash
   python - <<'PY'
   from seqreport import read_fasta
   for name in ("uniprot_human_subset", "gene_family_cycs", "qc_problems"):
       print(name, len(read_fasta(f"datasets/sample/{name}.fasta")))
   PY
   ```

   Expected: 60, 8, 8.

3. **Feed it the damaged file and write down what happened.** For
   `qc_problems.fasta`, your parser will do *something* about the empty record, the
   duplicate identifier, and the record containing `1`. State what your parser does
   for each, and whether that is what you intended before you tested it.

4. **Compare with `seqreport`.** Run `check_records` on the same file and list the
   defects the package finds. For each defect, decide: did your parser preserve
   enough information for that check to be possible at all?

   The interesting case is the duplicate identifier. If `to_dict` silently keeps the
   last record, you have destroyed the evidence. If it raises, your tool is awkward
   but honest. Which did you write?

5. **Add one check of your own** that `seqreport` does *not* have, with a test.
   Suggestions: header longer than 200 characters; sequence lines of unequal length;
   a record whose identifier contains a space (which is impossible under the spec and
   usually indicates a broken export).

6. **Measure the cost.** Time your parser against `seqreport.parse_fasta` on the
   largest file you can create quickly:

   ```bash
   python -c "
   from seqreport import read_fasta, write_fasta
   recs = read_fasta('datasets/sample/uniprot_human_subset.fasta')
   write_fasta([r for _ in range(200) for r in recs], '/tmp/big.fasta')
   "
   python -m timeit -n 3 -r 3 "from seqreport import read_fasta; list(read_fasta('/tmp/big.fasta'))"
   ```

   Report the ratio. If yours is more than 2× slower, say why; if it is faster, say
   whether it is doing less work.

## Deliverables

```text
p04/
├── my_fasta.py        # the parser, documented
├── test_my_fasta.py   # pytest tests, including one for each rule above
├── comparison.md      # the table: defect | your parser | seqreport | preserved evidence?
└── timing.txt         # the measured ratio, with the command that produced it
```

## Rubric (10 points)

| Criterion | Points | What earns full marks |
|---|---|---|
| Parser correct on all three files | 2 | 60/8/8 records, upper-cased, whitespace-free |
| Streaming, not slurping | 1 | Reads line by line; `read()` never used |
| Duplicate handling is a *decision*, justified | 2 | Either raise or keep-both, with the trade-off stated |
| Tests cover the five rules | 2 | Each rule has a test; the empty-record case is present |
| Own check + test | 2 | New defect found by the check, before the check was written |
| Timing measurement | 1 | Real numbers, real command, honest interpretation |

## Common wrong answers (instructor note)

1. **`data = f.read().split(">")`** — works, is one line, and is not streaming. It
   also loses the distinction between a record that ends with a newline and one that
   does not. Learners who take this shortcut must be asked to measure memory on a
   large file before it is accepted.
2. **Dropping empty records silently.** Now the empty record cannot be reported.
   A parser that "cleans" data has taken over the reviewer's job without telling them.
3. **`to_dict` with `dict[header] = seq`.** Duplicates collapse silently. This is the
   exact mechanism by which a `cat file >> file` accident becomes a doubled count in
   a published table.

## Extension

Make your parser gzip-aware (`gzip.open` when the suffix is `.gz`) and add a test that
generates a gzipped copy in a temporary directory. Then explain why detecting gzip by
*suffix* is a guess, and what the alternative (magic bytes) costs.
