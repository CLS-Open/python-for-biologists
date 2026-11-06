# Module 1 — Your environment, your evidence

> **Level:** beginner · **Time:** 3–4 hours · **Dataset:** `datasets/sample/gene_family_cycs.fasta`
> **Executable companion:** `notebooks/01_quality_control.ipynb` — every number in this module is produced there, and CI re-executes it on every push.

## 1. Scientific background

A computational result is not a result until someone else can reproduce it. That
sentence is easy to agree with and hard to implement, because most of what makes
an analysis reproducible lives *outside* the analysis: which Python, which
packages, which versions, which data file, which notebook cell was run after
which.

Sandve and colleagues' first rule for reproducible computational research is
blunt: *for every result, keep track of how it was produced*. Wilson and
colleagues' observation is equally blunt — scientists spend far more time reading
and re-running code than writing it, and most of the failures come from the
environment rather than from the science. The Jupyter-specific version of this
advice (Rule et al.) adds the trap that bites notebook users hardest: a notebook
records *what was executed and in what order*, and that order is often not the
order you see on screen.

This module therefore starts before any biology: a named environment, a pinned
install, a version you can print, and an exit code you can check. It is the least
exciting module in the course and the one that determines whether the other seven
are usable in six months.

## 2. Learning objectives

After this module you can:

1. Create an isolated Python environment, explain in one sentence why it exists,
   and demonstrate that installing a package there does not affect the system
   Python.
2. Run the `seqreport` command-line tool and interpret its **exit code**
   (`0`, `1`, `2`) as a machine-readable statement about the file it read.
3. Open a notebook, execute all cells from a clean kernel, and state why "it ran
   when I clicked through it" is not the same claim as "it runs top to bottom".
4. Print and record the exact versions of Python and the tools you used, and
   place that record next to your results.
5. Distinguish an error you can fix from an error you should report: a broken
   install, a broken environment, and a genuine defect look different, and the
   difference is usually in the first three lines of the message.

## 3. Required software

```bash
# Any OS with Python 3.10+ available. On Windows, use WSL2 (Ubuntu), because
# three of the eight modules use Unix tools that native Windows makes painful.
python3 --version         # expect: Python 3.10.x or newer
python3 -m venv .venv     # create an isolated environment in this directory
source .venv/bin/activate # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"    # from the repository root
seqreport --version       # expect: seqreport 0.1.0
```

If `seqreport --version` prints anything other than `seqreport 0.1.0`, stop here
and fix that before reading further. An environment you cannot verify is an
environment you cannot trust.

## 4. Conceptual explanation

### The interpreter, the environment, the kernel

Three things are routinely confused:

- **The interpreter** is the program that executes Python (`python3`). Its
  version matters because syntax and library behaviour change between versions.
- **The environment** is the set of packages the interpreter *can see*. Creating
  a virtual environment gives your project a private shelf of packages.
  `pip install` writes to that shelf, not to the system's.
- **The kernel** is the running interpreter that a notebook talks to. A notebook
  has no inherent connection to your terminal: it is a JSON file of cells, and
  something else — the kernel — executes them. That is why a notebook can hold
  stale state from a cell you deleted ten minutes ago.

### Why `pip install -e .` and not `pip install seqreport`

`-e` means *editable*: instead of copying the package into the environment, pip
records a link to the source directory. Edits to `src/seqreport/*.py` take effect
on the next import, with no reinstall. For learners this removes a whole class of
"I fixed it but nothing changed" confusion. For a published library you would use
a real install; for a course you want the link.

### Exit codes are the interface

A command that prints a report and exits `0` regardless of what it found is
useless in automation: CI cannot tell success from failure. `seqreport` therefore
uses three codes, and the lessons keep coming back to them:

| Code | Meaning | What to do |
|---|---|---|
| `0` | ran, and found no errors | proceed |
| `1` | ran, and the data has **errors** | read the report; the errors are named |
| `2` | could not run (missing file, malformed FASTA, bad argument) | fix the invocation, not the data |

The distinction between `1` and `2` is the difference between "your data is
wrong" and "your command is wrong". Those need different fixes, and a tool that
collapses them makes you guess.

### Determinism is a property you build, not a hope

Three habits, all of which this repository enforces in CI:

1. **Seeded randomness.** Any random draw gets an explicit seed, printed with the
   result.
2. **Sorted iteration.** Iterating a `set` or a `dict` built from one produces a
   different order between runs (hash randomisation), which changes plot bytes
   and file hashes. Sort before you iterate.
3. **No ambient metadata.** Timestamps, hostnames, absolute paths and library
   version strings written into output files make two identical analyses
   different. `scripts/make_figures.py` strips the Matplotlib version from every
   PNG for exactly this reason.

## 5. Mathematical and computational foundations

You need three facts about Python numbers here, because bioinformatics is
arithmetic and the arithmetic has rules.

**Integers are exact, floats are not.** A count of residues is an `int` and is
exact at any size. A molecular mass is a `float`: IEEE-754 double precision gives
about 15–17 significant decimal digits. Summing 105 residue masses accumulates
error in the last few digits, which is why the package rounds to 3 decimals in
reports instead of pretending to 12 digits of precision it does not have.

**Summation order changes the answer in the last bits.** For a protein mass the
difference is around 1e-10 Da — irrelevant here, and decisive in other contexts
(adding a million tiny terms to one huge one can lose the tiny ones entirely).

**A string is not a number.** `"1" + "2"` is `"12"`, not `3`. Sequence data
arrives as text, and silently arithmetic-ing text is one of the two or three
errors beginners make most. The type error Python raises (`TypeError: unsupported
operand type(s) for +: 'int' and 'str'`) is *helpful*; read it rather than
working around it.

Complexity, for the record: reading *n* records of total length *L* is O(L) time
and O(1) memory when streaming, O(L) memory when materialising. That difference is
the whole of Module 4.

## 6. Practical demonstration

```bash
# 1. Environment and version
source .venv/bin/activate
python --version
seqreport --version

# 2. Run the tool on real data; note the exit code, not just the output
seqreport stats datasets/sample/gene_family_cycs.fasta
echo "exit code: $?"

# 3. Same tool on a file with planted errors: the verdict changes
seqreport qc datasets/sample/qc_problems.fasta > /tmp/qc.md
echo "exit code: $?"      # 1, not 0 — the tool found errors and says so

# 4. A file that does not exist: an invocation error, not a data error
seqreport stats no_such_file.fasta
echo "exit code: $?"      # 2

# 5. The notebook, executed from a clean state rather than clicked through
jupyter lab notebooks/01_quality_control.ipynb
```

## 7. Expected output

```text
$ python --version
Python 3.10.13

$ seqreport --version
seqreport 0.1.0

$ seqreport stats datasets/sample/gene_family_cycs.fasta
id                length type            GC  GC-skew  AT-skew   mass (Da)
sp|P99999|CYC_HUMAN     105 protein          —        —        —    11,748.6
sp|P62897|CYC_MOUSE     105 protein          —        —        —    11,605.3
...
8 record(s); molecule type: protein
```

```text
$ seqreport stats no_such_file.fasta
error: no such file: no_such_file.fasta
exit code: 2
```

The `—` in the GC column is not missing data: GC content is undefined for a
protein, so the tool prints a dash rather than a number that would be meaningless.

## 8. Interpretation of results

- The eight masses are within ~11.7–12.4 kDa of each other. Cytochrome c is a
  small, highly conserved protein, and its mass is one of the few numbers in this
  course you can sanity-check against a textbook.
- The `type` column saying `protein` is a **guess** from composition, and Module 2
  makes the guess fail on purpose. Do not treat it as metadata.
- Exit code `1` on `qc_problems.fasta` means *the file has errors*, and the
  report names them. Exit code `0` on the clean subset means *these checks found
  nothing*. Those are different claims, and neither is "the data is correct".

What would falsify the environment claim? If `pip install -e .` succeeded but
`seqreport --version` printed nothing, then the entry point is not on the
environment's PATH — a real and common failure, covered in section 9.

## 9. Common errors and troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `command not found: seqreport` | The environment is not active, or the install went elsewhere | `which python` must point inside `.venv`; then `python -m pip install -e .` and retry |
| `ModuleNotFoundError: No module named 'seqreport'` inside a notebook | The notebook's kernel is a different interpreter from your terminal's | Check the kernel name in the top-right; register the venv with `python -m ipykernel install --user --name seqreport` |
| `error: externally-managed-environment` | Modern Debian/Ubuntu refuse system-wide pip installs | That is the feature working; use a venv |
| Notebook cells work individually but fail top to bottom | Stale kernel state; a name was defined in a cell that no longer exists | Kernel → Restart & Run All. This is the single most common notebook problem |
| `seqreport: error: the following arguments are required: file` | Missing positional argument | Read the usage line argparse printed; it is accurate |
| Encoding errors on Windows | Console code page vs UTF-8 | `set PYTHONUTF8=1`, or use WSL2 |
| `SyntaxError: invalid syntax` pointing at a line that looks fine | A stray character from copy-paste, or a mismatched bracket above | Look one line up; Python reports the point of *detection*, not always the cause |

## 10. Exercises

1. **Practical 1** ([`docs/practicals/practical-01-setup-and-first-report.md`](../practicals/practical-01-setup-and-first-report.md))
   — build the environment from scratch, prove isolation, and produce your first
   report. 45–60 minutes.
2. **Self-check (answer in the quiz):** you run `seqreport qc some_file.fasta`
   and get exit code `1` with two `error` lines. Is the file truncated? Not
   necessarily — name the second explanation and how you would tell them apart.
3. **Self-check:** write the one-line shell command that runs `pytest` and prints
   only its exit code. Why is that command more useful in CI than reading the
   test output by eye?
4. **Assignment 1** ([`docs/assessments/assignment-01-environment-log.md`](../assessments/assignment-01-environment-log.md))
   — produce a version log that a stranger could use to rebuild your environment.

## 11. Further reading and references

| Reference | Why read it |
|---|---|
| Sandve GK et al. *Ten Simple Rules for Reproducible Computational Research.* PLoS Comput Biol 2013. [10.1371/journal.pcbi.1003285](https://doi.org/10.1371/journal.pcbi.1003285) | Rules 1–4 are this module |
| Wilson G et al. *Best Practices for Scientific Computing.* PLoS Biol 2014. [10.1371/journal.pbio.1001745](https://doi.org/10.1371/journal.pbio.1001745) | Why "it runs" is not the bar |
| Rule A et al. *Ten simple rules for writing and sharing computational analyses in Jupyter Notebooks.* PLoS Comput Biol 2019. [10.1371/journal.pcbi.1007007](https://doi.org/10.1371/journal.pcbi.1007007) | The notebook-specific traps |
| Lee BD. *Ten simple rules for documenting scientific software.* PLoS Comput Biol 2018. [10.1371/journal.pcbi.1006561](https://doi.org/10.1371/journal.pcbi.1006561) | What an install section owes a reader |

All links verified via Crossref on 2026-11-06; see [`docs/references.md`](../references.md).

## 12. What this module does not teach

- **Containers.** Docker/Singularity solve environment reproducibility more
  thoroughly than a venv and add their own failure modes. Out of scope;
  Module 8 mentions them only to say when they are worth it.
- **`conda`.** Widely used in this field and a legitimate alternative. We use
  `venv` + `pip` because it ships with Python, so there is one less thing to
  install before the first success.
- **CI configuration.** The repository has it (`.github/workflows/ci.yml`), and
  Module 7 reads it, but writing GitHub Actions from scratch is not taught here.
- **Jupyter extensions, widgets and magic syntax.** Deliberate: they are usually
  the first thing copied from a blog and the first thing that breaks the notebook
  for everyone else.

## 13. Glossary

| Term | Meaning in this course |
|---|---|
| **environment** | A private set of installed packages that one interpreter can see |
| **kernel** | The live interpreter a notebook executes cells in |
| **exit code** | The integer a program returns; `0` success, non-zero failure |
| **deterministic** | Same inputs → byte-identical outputs, every run, every machine |
| **editable install** (`-e`) | Package resolved from the source directory, not copied into site-packages |
| **hash randomisation** | Python randomises `str` hashes per process, so `set` order changes between runs |
