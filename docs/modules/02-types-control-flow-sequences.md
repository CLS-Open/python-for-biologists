# Module 2 — Types, control flow and the shape of a sequence

> **Level:** beginner · **Time:** 4–5 hours · **Dataset:** `datasets/sample/uniprot_human_subset.fasta`, `datasets/sample/gene_family_cycs.fasta`
> **Executable companion:** `notebooks/01_quality_control.ipynb` (sections 1–2) and the examples below, all of which CI reproduces.

## 1. Scientific background

Almost every question a biologist asks of a sequence in Python reduces to four
operations on a string of letters: count things, compare things, slide a window
over them, and decide something per position. GC content is a count over a
windowed subset. A mutation is a comparison at one position. An ORF search is a
scan with a state. A quality filter is a decision per record.

The biology enters through the *alphabet*, and the alphabet is where beginners
get hurt. Nucleotide sequences contain ambiguity codes (`N`, `R`, `Y`, …).
Protein sequences contain `X`, `B`, `Z` and sometimes `U` (selenocysteine) and `O`
(pyrrolysine) — real residues, not errors. FASTA files contain lowercase, spaces
and Windows line endings. Every one of those has a defensible treatment and an
indefensible one: silently coercing them to uppercase and pretending the problem
does not exist is the indefensible one, because the coercion destroys the evidence
that something in the file needed attention.

## 2. Learning objectives

After this module you can:

1. Choose correctly between `str`, `list`, `tuple`, `dict` and `set` for a given
   biological task, and say what each choice costs.
2. Compute GC content with either denominator (all residues, or unambiguous
   only) and explain when the two differ by more than rounding.
3. Write a loop and a comprehension that produce the same result, then say which
   one you would defend in a code review and why.
4. Use `if`/`elif`/`else` and boolean logic to classify a record, and identify the
   case where a chain of `if`s silently swallows an impossible value.
5. Explain why `set` iteration order changes between runs, and show a bug it
   causes (non-reproducible output) and its fix (sort first).

## 3. Required software

Same environment as Module 1 (Python 3.10+, `seqreport` installed editable). This
module runs entirely in the Python REPL or a notebook — no new packages:

```bash
source .venv/bin/activate
python            # or: jupyter lab
```

## 4. Conceptual explanation

### Strings are sequences, and that is the point

A Python `str` is an immutable sequence of Unicode code points. "Immutable" means
`seq[0] = "A"` is an error, and every "modification" creates a new string. For
sequence data this is usually what you want: the original record stays intact
while you derive an upper-cased, whitespace-free copy — which is precisely why
`seqreport.Record` stores both `sequence` and `raw_sequence`.

Two consequences worth internalising:

- `"ACGT" * 3` and `slicing` (`seq[3:9]`, `seq[::3]`) are the workhorses. Frame 2
  of a nucleotide sequence is literally `seq[1:]`.
- Slicing never raises on out-of-range: `"ACGT"[10:20]` is `""`. Many a silent bug
  is a slice that returned nothing because an index was off by one.

### Choosing a container

| Need | Container | Why |
|---|---|---|
| Ordered residues, immutable | `str` | compact, sliceable, hashable |
| Ordered, mutable | `list` | append/extend while building results |
| Fixed-shape record (id, sequence) | `tuple` or dataclass | cannot be accidentally reordered |
| Count per residue | `dict` (or `collections.Counter`) | O(1) lookup by residue |
| Membership / deduplication | `set` | O(1) `in`, and **unordered** |

That last row is the trap. `{"A", "C", "G", "T"}` has no defined iteration order,
and Python deliberately randomises it per process for strings. Code that iterates
a set to produce output will produce *different output bytes* on different runs —
which is how figure files start drifting in a repository.

### Loop or comprehension?

Both are fine; comprehensions are usually clearer when the body is one
expression and there is no early exit. A loop is clearer when you accumulate
several things at once or need `break`. Write whichever a reader can check against
the written formula, and do not nest comprehensions more than one level — a nested
comprehension in a teaching repository is a bug in the teaching.

### `if` chains and impossible values

```python
if gc > 0.6:
    label = "GC-rich"
elif gc > 0.4:
    label = "typical"
else:
    label = "AT-rich"
```

This is wrong for a protein, and it *cannot tell you* it is wrong — `gc` would be
a number for a protein only if someone computed one. The fix is not a longer
`if` chain; it is refusing to compute the number at all (see
`guess_molecule_type` and the `—` in the report). Refusing is a design decision
you make once and benefit from everywhere.

## 5. Mathematical and computational foundations

**GC content**, two conventions, both defensible:

$$
\mathrm{GC}_{\text{acgt}} = \frac{G + C}{A + C + G + T + U}
\qquad
\mathrm{GC}_{\text{all}} = \frac{G + C}{A + C + G + N + T + U + \ldots}
$$

For `GGCCNNNN` these give **1.000** and **0.500** — a factor of two, not a
rounding difference. For real sequencing data with 1% ambiguous bases the two
differ in the second decimal place, which is exactly the size of difference people
report as a finding.

**Skew** is a normalised difference:

$$
\text{GC skew} = \frac{G - C}{G + C}
$$

and is **undefined** when the denominator is zero. Returning `0.0` would assert
"no skew", which is a different statement from "no G or C to compute a skew from".
The package returns `None`, and the reporter prints a dash.

**Windowed statistics.** A sequence of length *L* with window *w* and step *s*
produces ⌈(L − w)/s⌉ + 1 full windows plus, usually, one partial window at the
end. The partial window is computed over fewer residues and is **not comparable**
with the others; `seqreport.windowed_gc` flags it (`complete: False`) instead of
quietly averaging it in. Cost: O(L) time, O(L/w) output.

**A numeric trap worth naming.** `sum(c == "G" for c in seq)` works because
`True == 1` in Python. It is idiomatic and correct, and it is worth knowing that
you are relying on booleans being integers.

## 6. Practical demonstration

```python
from seqreport import read_fasta, composition, gc_content, gc_skew, windowed_gc

records = read_fasta("datasets/sample/gene_family_cycs.fasta")
human = records[0]

# 1. Counting: a dict, most common first
counts = composition(human.sequence)
print(list(counts.items())[:5])

# 2. A loop and a comprehension that agree
total_loop = 0
for aa in human.sequence:
    if aa in "ACGT":
        total_loop += 1
total_comp = sum(1 for aa in human.sequence if aa in "ACGT")
print(total_loop, total_comp, total_loop == total_comp)

# 3. Slicing: six frames are just offsets
dna = "ATGGCTAGCTAA"
frames = [dna[i:] for i in range(3)]
print(frames)

# 4. The denominator question, on an ambiguous sequence
for denom in ("acgt", "all"):
    print(denom, round(gc_content("GGCCNNNN", denominator=denom), 3))

# 5. Undefined is not zero
print("GC skew of AATT:", gc_skew("AATT"))

# 6. Windows, and the partial last window
windows = windowed_gc("ACGT" * 26, window=20)      # 104 nt, so the last is partial
print(windows[0], windows[-1])
```

## 7. Expected output

```text
[('K', 18), ('G', 13), ('E', 8), ('I', 8), ('T', 7)]
28 28 True
['ATGGCTAGCTAA', 'TGGCTAGCTAA', 'GGCTAGCTAA']
acgt 1.0
all 0.5
GC skew of AATT: None
{'start': 0, 'end': 20, 'gc': 0.5, 'complete': True} {'start': 100, 'end': 104, 'gc': 0.5, 'complete': False}
```

Note the third frame output: `dna[2:]` is `"GGCTAGCTAA"` — 10 characters, not 11.
Slicing past the end does not raise; it truncates. That is the off-by-one trap in
the flesh.

## 8. Interpretation of results

- The most common residue in human cytochrome c is **lysine (18 of 105)**. That is
  a real, well-known feature of the protein (it is highly basic, which is how it
  binds a negatively charged cytochrome oxidase surface), and it is the kind of
  claim you can check against a textbook rather than trusting the code.
- `gc_content("GGCCNNNN")` returning two different numbers for two conventions is
  not a bug in either. Any report of "GC content" must name its denominator; this
  course always does.
- `gc_skew("AATT")` returning `None` means "undefined", not "zero". If you need a
  number for plotting, *you* choose what an undefined value looks like — the
  library will not choose for you.
- The last window is `start: 100, end: 104, complete: False`: only 4 of its 20
  residues exist. Its GC (0.5) happens to be right here, and in general it is
  computed over a different number of residues than every other window, so it is
  flagged rather than silently averaged in. `gc` is `None` (not `0.0`) only when a
  window contains no unambiguous base at all.

What would falsify the "counting" claim? Any disagreement between the loop and the
comprehension. That is a self-check, not proof: both could be wrong in the same
way. The Biopython cross-validation script is the independent check.

## 9. Common errors and troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `TypeError: unsupported operand type(s) for +: 'int' and 'str'` | Arithmetic on text | Convert deliberately: `int(x)`, and decide what a non-numeric value should mean |
| `IndexError: string index out of range` | Direct indexing past the end (`seq[i]`) | Slicing instead (`seq[i:i+1]`) returns `""`; or check `i < len(seq)` |
| `AttributeError: 'str' object has no attribute 'append'` | Strings are immutable; `+=` on a string in a loop is also O(n²) | Accumulate in a list, `"".join(...)` at the end |
| GC > 1 computed | Denominator is wrong, often counting only G/C twice | Write the formula next to the code; test with a hand-computed example |
| Output differs between runs, same input | Iterating a `set`/`dict` | `sorted(...)` before iterating; never rely on hash order |
| `KeyError` from `counts[aa]` | Residue absent from the dict | `counts.get(aa, 0)` — and know that `defaultdict(int)` would hide typos |
| `ZeroDivisionError` on an empty sequence | GC of `""` | Refuse explicitly with a clear message, as the package does |

## 10. Exercises

1. **Practical 2** ([`docs/practicals/practical-02-composition-by-hand.md`](../practicals/practical-02-composition-by-hand.md)):
   compute composition and mass for three records by hand and by code, and make
   the two disagree on purpose to see which is wrong.
2. **Self-check:** `len(set("ACGTACGT"))` — predict the value, then check. Why is
   this *not* a way to count distinct *k*-mers?
3. **Self-check:** write a one-liner that returns the fraction of `X` residues in
   a protein, and state what it returns for an empty sequence.
4. **Challenge 1** ([`docs/assessments/challenge-01-ambiguous-alphabets.md`](../assessments/challenge-01-ambiguous-alphabets.md)):
   design and defend an alphabet validator that accepts IUPAC nucleotide codes and
   rejects the rest.
5. **Assignment 2** ([`docs/assessments/assignment-02-composition-report.md`](../assessments/assignment-02-composition-report.md)):
   a reproducible composition report for the 60-protein subset.

## 11. Further reading and references

| Reference | Why read it |
|---|---|
| Cock PJA et al. *Biopython: freely available Python tools for computational molecular biology and bioinformatics.* Bioinformatics 2009. [10.1093/bioinformatics/btp163](https://doi.org/10.1093/bioinformatics/btp163) | The library we validate against, and a model of sequence data structures |
| NCBI. *International Nucleotide Sequence Database Collaboration (INSDC) feature table.* [INSDC specification](https://www.insdc.org/submitting-standards/feature-table/) | Where ambiguity codes are actually defined |
| NC-IUB. *Nomenclature for incompletely specified bases in nucleic acid sequences: recommendations 1984.* Nucleic Acids Res 1985;13:3021. [10.1093/nar/13.9.3021](https://doi.org/10.1093/nar/13.9.3021) | The original `N`/`R`/`Y`/`K`/`M`/`S`/`W`/`B`/`D`/`H`/`V` table |

## 12. What this module does not teach

- **`numpy` and vectorisation.** Module 6 introduces arrays; here everything is
  plain Python so that the data structures are visible.
- **Streaming large files.** A separate concern, Module 4.
- **Alignment or translation algorithms.** Repository #4
  (`bioinformatics-foundations`) is where those live, deliberately: this course's
  subject is Python, and duplicating the algorithms here would teach both worse.
- **Regex.** Useful and dangerous on sequence data (a regex can silently match
  across a record boundary). Module 3 covers the one case where it is the right
  tool, and the lesson names the danger.

## 13. Glossary

| Term | Meaning in this course |
|---|---|
| **immutable** | Cannot be changed in place; every "change" makes a new object |
| **ambiguity code** | A letter standing for more than one residue (`N`, `R`, `Y`, `X`) |
| **denominator** | What you divide by: here, all residues or only unambiguous ones |
| **comprehension** | `[f(x) for x in xs if p(x)]` — a loop that builds a collection |
| **off-by-one** | An index or length that is one too small or too large; the classic slice bug |
| **hash order** | The iteration order of a `set`/`dict`, which Python randomises per process |
