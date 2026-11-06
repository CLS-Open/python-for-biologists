# Quiz 01 — Modules 1–3

**Time:** 20 minutes · **Closed book** · **10 questions, 10 points** · **Answer key at the end**

Answer without running anything. If a question cannot be answered from the modules,
that is a defect in the modules — say so.

---

**1.** (1 pt) A script reports `GC content: 50.0%` for a 200-base sequence containing
12 `N` bases. What information is missing, and how large could the error be?

**2.** (1 pt) `seqreport qc file.fasta` exits with code `1`. Name two structurally
different explanations and the observation that distinguishes them.

**3.** (1 pt) True or false, with a one-line reason: *"If all tests pass, the code is
correct."*

**4.** (1 pt) What does `gc_skew("AATT")` return, and why is that better than `0.0`?

**5.** (1 pt) A peptide has 20 residues. How many water molecules are subtracted when
computing its molecular weight, and how many would be subtracted for a *cyclic*
peptide? State the difference in daltons.

**6.** (1 pt) Name the container you would use for each task, and say why:
(a) counting occurrences of each residue; (b) collecting issues found while scanning
records; (c) checking whether a residue is one of the 20 standard ones.

**7.** (1 pt) Write the one-line fix for this, and name the underlying Python rule:

```python
def add(issue, issues=[]):
    issues.append(issue)
    return issues
```

**8.** (1 pt) Why does `"ACGT"[2:]` give `"GCT"` rather than raising, and what class of
bug does that behaviour make possible?

**9.** (1 pt) You run the same analysis twice on the same input and the PNG files
differ in bytes. Name the three most likely causes, in the order you would check them.

**10.** (1 pt) A library function you use catches `Exception`, prints "problem with
record", and returns `None`. Give one concrete way this could produce a wrong
scientific conclusion.

---

## Answer key

**1.** The denominator. Over unambiguous bases only, GC/ACGTU; over all bases, GC/200.
If the 12 `N` are all non-GC, the two differ by about 6 percentage points (12/188 vs
12/200 of the denominator), and the reported "50%" could be 50% or 47% depending on
convention. The report must name the denominator (Module 2 §5).

**2.** (i) The file has genuine errors — the report names them, e.g. an
`invalid_character` or `empty_sequence` issue. (ii) The file has no errors but a
threshold you imposed is being reported as an error, e.g. a rule you added. The
distinguishing observation: read the issue list. Code `1` never means "cannot read
the file" — that is code `2` (Module 1 §4). A third correct answer: the file mixes
errors and warnings and you only looked at the total count.

**3.** False. Tests are evidence, not proof: they can all pass while the code is wrong
on an input nobody tested, and they can encode the same misunderstanding as the code.
`seqreport`'s tests pass *and* it is cross-validated against Biopython precisely
because of this (Module 3 §5, `docs/validation.md`).

**4.** `None`, because there is no G or C, so `(G−C)/(G+C)` has a zero denominator.
`0.0` would assert "balanced G and C", which is a measurement; `None` asserts "not
measurable", which is the truth (Module 2 §5).

**5.** \(n-1 = 19\) waters for a linear peptide; 20 for a cyclic one (one more bond,
one more condensation). Difference: 1 × 18.0153 = **18.0153 Da** (Module 2 §5).

**6.** (a) `dict`/`Counter` — O(1) lookup by residue. (b) `list` — ordered,
appendable, duplicates are meaningful (two issues of the same code are two issues).
(c) `set` or a frozen set — O(1) membership and set arithmetic; and note that you must
not iterate it for output (Module 2 §4).

**7.** `def add(issue, issues=None):` then `if issues is None: issues = []`. The rule:
default arguments are evaluated **once**, at function definition, so a mutable default
is shared between calls (Module 3 §4, §9).

**8.** Slicing clamps rather than raising: `str.__getitem__` with a slice returns
whatever exists. The bug class is the **off-by-one** that produces a shorter (or empty)
result instead of an error — a frame that silently loses its last base, a window that
silently shrinks (Module 2 §7).

**9.** (1) Library metadata written into the file (Matplotlib version string, date);
strip it with `metadata={"Software": None}`. (2) Iteration over a `set`/`dict` whose
order depends on hash randomisation; sort first. (3) Unseeded randomness or a
timestamp in the content or the path. Check in that order because (1) is silent and
certain, (2) is intermittent, and (3) is usually visible in the code (Module 1 §4,
practical 05).

**10.** Example: a record with an invalid residue is skipped, `None` is returned, the
caller filters out `None` values, and the mean molecular weight is computed over 59 of
60 records — with no record in the output saying which one vanished or why. The wrong
conclusion is a composition statistic that silently excludes the one outlier that
mattered. (Second acceptable answer: the error is printed to stdout, the pipeline
reads stdout as data, and the message becomes a "value".)

---

## Marking notes for instructors

- Questions 2 and 9 are the discriminators: they test whether a learner can reason
  about *failure* rather than recall syntax. Expect partial credit to be common.
- Question 5 catches the single most frequent arithmetic error in the course (using
  `n` instead of `n−1`). If more than a third of a cohort misses it, re-run practical
  02's hand calculation.
- Question 10 has many correct answers; mark the *mechanism*, not the example.
