# Practical 03 — Traceback forensics

**Module:** 3 · **Level:** L2 (guided) · **Time:** 60 min · **Dataset:** none (five broken programs you fix)

## Aim

Fix five broken programs from their tracebacks alone, and state for each one
whether the bug was in the *call*, the *function*, or the *assumption*.

## Instructions

Create `p03/` with the five files below, exactly as written. Each contains one
mistake. Run each with `python file.py`, read the traceback **from the bottom up**,
and fix the cause — not the line that happens to raise.

### `bug1.py` — the mutable default

```python
def add_issue(issue, issues=[]):
    issues.append(issue)
    return issues

print(add_issue("first"))
print(add_issue("second"))
print(add_issue("third"))
```

Expected (wrong) output: three lists, growing. Expected (right) output: three
one-element lists. **Question:** why does the list survive between calls?

### `bug2.py` — the keyword-only argument

```python
from seqreport import gc_content
print(gc_content("GGCCNNNN", "all"))
```

**Question:** what does the error message tell you that the function signature in
`docs/modules/03-functions-modules-errors.md` §4 already told you?

### `bug3.py` — catching the wrong thing

```python
from seqreport import read_fasta

def count_records(path):
    try:
        return len(read_fasta(path))
    except Exception:
        return 0

print(count_records("datasets/sample/gene_family_cycs.fasta"))
print(count_records("does_not_exist.fasta"))
```

This "works". **Question:** what has it just done to the meaning of the number `0`,
and what should it do instead?

### `bug4.py` — the off-by-one

```python
from seqreport import read_fasta

records = read_fasta("datasets/sample/gene_family_cycs.fasta")
for i in range(len(records) + 1):
    print(i, records[i].accession)
```

**Question:** the traceback names `IndexError` at the last line. Which line actually
contains the bug?

### `bug5.py` — the silent type error

```python
from seqreport import read_fasta

records = read_fasta("datasets/sample/uniprot_human_subset.fasta")
total = 0
for rec in records:
    total += rec.sequence
print(len(total))
```

**Question:** `len()` of what? Fix this twice — once by summing lengths, once by
building a single concatenated string — and say which you would defend in review.

## Instructions (continued)

1. For each bug, save the **original traceback** (stderr) to `tracebacks/bugN.txt`
   before fixing anything. The traceback is evidence; keep it.
2. For each bug, write in `fixes.md`: the file and line where the *cause* is, the
   category (`call` / `function` / `assumption`), the one-line fix, and one sentence
   on how a test would have caught it earlier.
3. Fix `bug3.py` so that a missing file still fails loudly, and demonstrate the new
   behaviour with a captured run.

## Deliverables

```text
p03/
├── bug1.py … bug5.py          # fixed versions
├── tracebacks/bug1.txt … bug5.txt   # the original stderr, unedited
└── fixes.md                   # the table described above
```

## Rubric (10 points)

| Criterion | Points | What earns full marks |
|---|---|---|
| Tracebacks preserved before fixing | 2 | Five files, each the genuine stderr |
| Cause correctly located for all five | 3 | Line number of the cause, not of the raise, where they differ |
| Fixes are minimal and correct | 2 | No rewriting of the program to avoid the concept |
| bug3 fixed to fail loudly | 2 | Missing file raises/reports; valid file still counted |
| "How a test would have caught it" is specific | 1 | Names the test, the input and the assertion |

## Common wrong answers (instructor note)

1. **bug1: "Python is caching the list."** It is not caching; the default is
   evaluated once, at function definition, and shared. The fix is `issues=None` plus
   `if issues is None: issues = []` — never `issues=[]`.
2. **bug4: "the loop bound is wrong on line 4".** The `IndexError` appears on the
   `print` line because that is where the invalid index is *used*, but the count is
   wrong on the `range(...)` line. Reading a traceback means asking "which value was
   wrong, and where was it made?"
3. **bug3: "catch everything, it's safer."** It converts "I could not read the file"
   into "the file has zero records" — two different facts, and a downstream
   percentage computed from 0 records is now silently meaningless. Catch
   `FastaError`, and re-raise the rest.
4. **bug5: "`total += rec.sequence` should work."** It raises `TypeError` on the
   first iteration: `int + str`. If a learner "fixes" it with `str(total)`, they have
   built a concatenation that happens to look like arithmetic; the review question
   is which one the variable name promises.

## Extension

Add `tests/test_bugfixes.py` with one test per bug, each asserting the *fixed*
behaviour, and run `pytest -q`. Then re-introduce one bug and confirm the test
fails — a test you have never seen fail is a test you do not know works.
