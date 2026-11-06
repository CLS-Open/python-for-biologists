# Module 3 — Functions, modules and the discipline of failing well

> **Level:** beginner → intermediate · **Time:** 5–6 hours · **Dataset:** `datasets/sample/qc_problems.fasta`
> **Executable companion:** `notebooks/01_quality_control.ipynb` (section 3) plus the snippets below, which CI reproduces.

## 1. Scientific background

The difference between a script that worked once and a tool that other people can
use is almost entirely about **boundaries**: what a function promises, what it does
when the promise cannot be kept, and what the caller is allowed to assume. In
bioinformatics the failing inputs are not exotic — truncated downloads,
half-written files, records that were concatenated twice, headers from three
different databases in one file. A tool that returns a plausible number for a
broken record is more dangerous than one that stops, because the number goes into
a figure and the figure goes into a paper.

Lee's rules for documenting scientific software and Wilson's best-practices paper
both make the same point from different directions: the *interface* is the
product. This module is about building that interface in Python — small functions,
explicit errors, and a module layout that lets a stranger find their way in.

## 2. Learning objectives

After this module you can:

1. Write a function with a docstring, type hints and a doctest, and explain which
   of the three is a contract, which is a check, and which is documentation.
2. Distinguish a **ValueError** (the input is wrong) from a **TypeError** (the
   caller used the wrong kind of thing) and raise the right one.
3. Define a custom exception, catch it at exactly one place in a program, and
   explain why catching it in two places is a defect rather than belt-and-braces.
4. Split a growing script into modules under `src/`, expose a small public API via
   `__init__.py`, and use an `if __name__ == "__main__":` guard correctly.
5. Read a traceback from the bottom up, name the frame where the mistake actually
   happened, and fix the cause rather than the symptom.

## 3. Required software

```bash
source .venv/bin/activate
python -m pip install -e ".[dev]"     # includes pytest
seqreport qc datasets/sample/qc_problems.fasta; echo "exit=$?"
```

## 4. Conceptual explanation

### A function is a promise

```python
def gc_content(sequence: str, *, denominator: str = "acgt") -> float:
```

Everything in that line is part of the promise: it takes a string, it returns a
float, and the denominator is a keyword-only choice with a documented default.
The docstring says what happens when the denominator is zero (it raises). A caller
who reads nothing else can still use the function correctly.

**Pure functions are testable functions.** `gc_content(seq)` depends on nothing but
its argument: no file, no clock, no global state. That is why it has a hand-checked
test and a doctest. `parse_fasta(path)` is impure by nature — it touches the disk —
so its tests use temporary files and committed fixtures.

### Keyword-only arguments are a bug barrier

The `*` in `gc_content(seq, *, denominator=...)` means the denominator cannot be
passed positionally. `gc_content(seq, "all")` is a `TypeError`; you must write
`denominator="all"`. In a function with two plausible single-letter choices, that
one character prevents the class of bug where the arguments get swapped and the
answer is wrong but not obviously wrong.

### Exceptions: who is responsible?

| Situation | Exception | Whose fault |
|---|---|---|
| Input is syntactically fine but semantically impossible (`gc_content("")`) | `ValueError` | caller's |
| Input is the wrong type (`gc_content(None)`) | `TypeError` | caller's |
| File does not exist | `FastaError` (a `ValueError`) | caller's |
| Disk full while writing | `OSError` | nobody's; propagate |

The rule: **raise where the problem is detected, catch where it can be handled**.
A library should almost never catch a programming error; it should let it travel.
`seqreport` raises `FastaError` deep in the parser and lets the CLI decide what it
means for the process (exit code 2, message on stderr).

### Catch once, in one place

An early version of the CLI caught `FastaError` in the file loader *and* in
`main()`. The second handler was dead code: no test could reach it, coverage could
not see it, and a future change that needed to intercept the error would have
edited the wrong one. The fix was to delete the inner handler. **Duplicate error
handling is not defensive programming; it is untested code with a reassuring
name.**

### `raise ... from None`

```python
try:
    value = float(text)
except ValueError:
    raise ValueError(f"{text!r} is not a number") from None
```

`from None` suppresses the chained "During handling of the above exception…"
block. Use it when the original exception adds nothing for the reader. Do **not**
use it to hide a cause you do not understand.

### Module layout

```
src/seqreport/
├── __init__.py     # the public API: what `from seqreport import ...` gives you
├── records.py      # parsing and writing
├── composition.py  # statistics
├── qc.py           # checks
├── report.py       # rendering
└── cli.py          # argument parsing and process exit codes
```

The `src/` layout is deliberate: it makes the installed package distinct from the
repository root, so `import seqreport` can only succeed if the package was
installed — which is exactly the condition you want to be true when a learner says
"it works for me".

## 5. Mathematical and computational foundations

**Complexity of what you just wrote.** `check_records` is O(n·L) in records and
residues for the per-record checks, plus O(n) for the duplicate scan, plus
O(i log i) to sort *i* issues. Sorting is not free: with 60 records it is
invisible; with 2 million short reads it is the dominant cost, and the fix is to
bucket by severity rather than sort.

**Why the checks return data, not print.** Returning `list[Issue]` makes the
checks testable (assert on the list) and composable (render as text, JSON, HTML).
A function that prints cannot be tested without capturing stdout and cannot be
reused by the next renderer. This is the single most useful refactor in the
module: `print` in a library is a bug.

**Idempotence.** Running the same check twice on the same records must give the
same list. If it does not, something is keeping state — a cache, a counter, a
mutable default argument. (Mutable defaults are the classic Python trap:
`def f(x, acc=[])` shares one list across every call.)

## 6. Practical demonstration

```python
from seqreport import read_fasta, check_records, FastaError
from seqreport.qc import CheckOptions

# 1. A check that returns data instead of printing it
records = read_fasta("datasets/sample/qc_problems.fasta")
issues = check_records(records)
print(len(issues), "issues")
print(type(issues[0]).__name__, issues[0].code, issues[0].severity)

# 2. Options are an object, not five booleans threaded through every call
lenient = check_records(records, CheckOptions(min_length=10, allow_duplicate_ids=True))
print(len(issues), "->", len(lenient), "issues with a different rule set")

# 3. The library raises; the CLI decides what that means
try:
    read_fasta("no_such_file.fasta")
except FastaError as exc:
    print("caught a FastaError:", exc)

# 4. A pure function with a doctest can be checked in place
from seqreport.composition import gc_content

def at_fraction(seq: str) -> float:
    """Fraction of residues that are A or T.

    >>> round(at_fraction("ATGC"), 3)
    0.5
    """
    seq = seq.upper()
    if not seq:
        raise ValueError("AT fraction is undefined for an empty sequence")
    return (seq.count("A") + seq.count("T")) / len(seq)

print(round(at_fraction("ATGC"), 3))
```

## 7. Expected output

```text
7 issues
Issue invalid_character error
7 -> 6 issues with a different rule set
caught a FastaError: no such file: no_such_file.fasta
0.5
```

```text
$ seqreport qc datasets/sample/qc_problems.fasta > /dev/null
$ echo "exit=$?"
exit=1
```

With `min_length=10` and duplicates allowed, exactly one issue disappears — the
`duplicate_id` error, which was permitted — for 7 → 6. Nothing else changes,
because no record in this file is shorter than 10 residues. If a second issue had
vanished, the option plumbing would be passing the wrong thing; checking the
*difference* rather than the total is how you notice that.

(And note which issue sorted first: `invalid_character`, because issues sort by
severity, then by record id — `P62898|pl_invalid_residue` precedes
`P99999|pl_duplicate` alphabetically. Ordering rules that you cannot state are
ordering rules you cannot rely on.)

## 8. Interpretation of results

- **Seven issues for eight records** is not "seven problems". One identifier
  duplicate is a single file-level problem reported once, and one record
  (`pl_truncated`) is clean: it is short but legitimate, and `min_length=20` does
  not flag a 60-residue protein. A checker whose counts you cannot explain is a
  checker you will start ignoring.
- **Changing the options changed two results, not the code.** That is the point of
  passing a `CheckOptions` object: thresholds are data, and data can be recorded in
  the report (`report.options`) so a reader knows which rules produced the verdict.
- **The library raised; the CLI translated.** `FastaError` in, exit code 2 out —
  and a human-readable line on stderr that names the file. The biology code knows
  nothing about exit codes.
- What would falsify "the checks are correct"? A record whose defect is real and
  unreported, or a record flagged for something it does not do. The shipped
  dataset makes both directions checkable, because the defects are documented in
  `datasets/metadata/qc_problems.yml` and the clean subset produces zero issues.

## 9. Common errors and troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `NameError: name 'x' is not defined` | Typo, or defined inside a function and used outside | Check scope; the traceback's last frame is where the name was *used* |
| `IndentationError` / `TabError` | Mixed tabs and spaces from copy-paste | Configure the editor to insert 4 spaces; never both |
| `TypeError: gc_content() takes 1 positional argument but 2 were given` | Keyword-only argument passed positionally | Write `denominator="all"` |
| `UnboundLocalError` | A name assigned later in the function but read earlier | Move the assignment, or make it a parameter |
| Exception caught but the program still crashes | `except` of the wrong class (`Exception` shadowing) | Catch the narrowest class; print it while debugging |
| `if __name__ == "__main__"` block never runs | Module was imported, not executed | Run `python -m seqreport.cli`, not `python seqreport/cli.py` |
| Doctest fails on whitespace | Trailing spaces or dict ordering in the expected text | Compare printed values with explicit `round()`, or assert a `set` |
| Exit code 0 but wrong output | The program printed an error instead of raising | Never report failure by printing; return a code or raise |

## 10. Exercises

1. **Practical 3** ([`docs/practicals/practical-03-traceback-forensics.md`](../practicals/practical-03-traceback-forensics.md)):
   five broken programs, five tracebacks, five fixes — each one a real mistake
   from this project's development.
2. **Self-check:** `def f(x, cache={}): cache[x] = True; return cache` — what does
   the third call return, and why? (Mutable default argument.)
3. **Self-check:** write a function `median_length(records)` that raises
   `ValueError` on an empty list. Then write the test that proves it raises, not
   the test that proves it returns `0`.
4. **Assignment 3** ([`docs/assessments/assignment-03-mini-tool.md`](../assessments/assignment-03-mini-tool.md)):
   a small module with three functions, docstrings, doctests and a CLI.
5. **Challenge 2** ([`docs/assessments/challenge-02-fail-loudly.md`](../assessments/challenge-02-fail-loudly.md)):
   take a permissive parser and make it fail loudly without becoming unusable.

## 11. Further reading and references

| Reference | Why read it |
|---|---|
| Lee BD. *Ten simple rules for documenting scientific software.* PLoS Comput Biol 2018. [10.1371/journal.pcbi.1006561](https://doi.org/10.1371/journal.pcbi.1006561) | The docstring/README contract |
| Wilson G et al. *Best Practices for Scientific Computing.* PLoS Biol 2014. [10.1371/journal.pbio.1001745](https://doi.org/10.1371/journal.pbio.1001745) | Rules 5–8 are this module: modularity, naming, error handling |
| Beaulieu-Jones BK, Greene CS. *Reproducibility of computational workflows is automated using continuous analysis.* Nat Biotechnol 2017. [10.1038/nbt.3780](https://doi.org/10.1038/nbt.3780) | Why the checks must run on every change, not once |
| Python documentation. *Errors and Exceptions.* [docs.python.org/3/tutorial/errors.html](https://docs.python.org/3/tutorial/errors.html) | The reference for everything in section 4 |

## 12. What this module does not teach

- **Object-oriented design.** `seqreport` uses dataclasses where they earn their
  place and plain functions everywhere else. Inheritance, mixins and abstract base
  classes are not needed for this course and teaching them here would suggest they
  are.
- **Property-based testing** (`hypothesis`). Module 7 covers testing; this module
  only gets as far as doctests and explicit exceptions.
- **Packaging and publishing to PyPI.** Module 8 covers building and installing;
  uploading to a public index is out of scope.
- **Logging.** `logging` is the right answer for long-running pipelines and the
  wrong answer for a command that prints one report; the trade-off is named in
  Module 8, not taught here.

## 13. Glossary

| Term | Meaning in this course |
|---|---|
| **pure function** | Output depends only on arguments; no I/O, no globals, no clock |
| **keyword-only** | Argument after `*` that must be named at the call site |
| **exception chaining** | The "During handling of the above exception" context; suppress with `from None` |
| **`src/` layout** | Package inside `src/`, so imports only work when installed |
| **idempotent** | Running it twice changes nothing |
| **mutable default** | An argument default that is one shared object across calls — a trap |
