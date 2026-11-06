# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # From FASTA to a reproducible quality report
#
# **Repository 1 of 15, CLS-Open — `python-for-biologists`**
#
# This notebook does the whole job the package exists for, in the open, using the
# real data in `datasets/`:
#
# 1. parse FASTA records — and see what a real header actually contains;
# 2. compute composition statistics, and check one by hand;
# 3. run quality control on a file with deliberately planted defects;
# 4. write a report you can email to a collaborator.
#
# Every number printed below came from the data in this repository. Nothing here
# is typed in by hand, and the notebook is executed by CI on every push, so it
# cannot drift away from the code.

# %% [markdown]
# ## 0. Setup
#
# The notebook finds the repository root by walking upwards until it sees
# `pyproject.toml`. It never assumes the current working directory — that is the
# single most common reason a teaching notebook "works on my machine".

# %%
from pathlib import Path
import sys

start = Path.cwd().resolve()
for candidate in [start, *start.parents]:
    if (candidate / "pyproject.toml").is_file():
        REPO = candidate
        break
else:  # pragma: no cover - only when the notebook is run outside the repo
    raise RuntimeError("run this notebook from inside the repository")

sys.path.insert(0, str(REPO / "src"))
SAMPLE = REPO / "datasets" / "sample"
print("repository root:", REPO.name)
print("data files:", sorted(p.name for p in SAMPLE.glob("*.fasta")))

# %%
import seqreport
from seqreport import (
    build_report,
    check_records,
    composition,
    gc_content,
    gc_skew,
    molecular_weight,
    parse_fasta,
    read_fasta,
    to_markdown,
)

print("seqreport", seqreport.__version__)

# %% [markdown]
# ## 1. Parsing: what is really in a header
#
# The FASTA specification says only that the identifier is **the first
# whitespace-delimited token of the header line**. UniProt packs three fields
# into that token with `|` separators, and puts metadata after it in `KEY=value`
# form. So `record.id` is not an accession, and `record.description` is not a
# sentence — both are conventions layered on top of a very loose format.

# %%
records = read_fasta(SAMPLE / "gene_family_cycs.fasta")
first = records[0]

print("id          :", first.id)
print("accession   :", first.accession, "  <- convenience property, middle | field")
print("description :", first.description)
print("length      :", len(first), "residues")
print("first 40 aa :", first.sequence[:40])

# %% [markdown]
# `parse_fasta` is a generator: it hands you one record at a time, so a file
# larger than memory is fine. `read_fasta` builds a list, which is convenient and
# is the wrong tool for a 3 GB file. Both read the same bytes.

# %%
from itertools import islice

subset_path = SAMPLE / "uniprot_human_subset.fasta"
stream = parse_fasta(subset_path)

first_three = list(islice(stream, 3))
print("first three records without loading the file:")
for rec in first_three:
    print(f"  {rec.accession:10} {len(rec):4} aa")

remaining = sum(1 for _ in stream)
print(f"\n{len(first_three)} + {remaining} = {len(first_three) + remaining} records consumed in total")
print("at no point did the whole file exist in memory as parsed Record objects")

# %% [markdown]
# ## 2. Composition and molecular weight
#
# Molecular weight is the arithmetic you can check by hand: sum the residue
# masses, then remove one water (18.0153 Da) for every peptide bond. A peptide of
# *n* residues has *n − 1* bonds.

# %%
human = records[0]
counts = composition(human.sequence)
n = len(human.sequence)
mass = molecular_weight(human.sequence)

print(f"{human.accession}: {n} residues")
print("top residues:", list(counts.items())[:5])
print(f"molecular weight: {mass:,.2f} Da")

# %% [markdown]
# **Check the arithmetic.** Recomputed below from the residue table directly,
# without calling `molecular_weight`, so that a bug in the function cannot hide
# behind itself:

# %%
from seqreport.composition import RESIDUE_MASSES, WATER

by_hand = sum(RESIDUE_MASSES[aa] for aa in human.sequence) - (n - 1) * WATER
print(f"by hand          : {by_hand:,.6f} Da")
print(f"from the package : {mass:,.6f} Da")
print("agreement        :", abs(by_hand - mass) < 1e-9)

# %% [markdown]
# An independent implementation is a different kind of evidence from a hand
# calculation, and worth having both. If Biopython is installed, compare:

# %%
try:
    from Bio.SeqUtils import molecular_weight as bio_mass
except ImportError:
    print("Biopython not installed — the cross-validation script covers this in CI")
else:
    print(f"Biopython: {bio_mass(human.sequence, 'protein'):,.6f} Da")
    print("agreement:", abs(bio_mass(human.sequence, 'protein') - mass) < 1e-6)

# %% [markdown]
# ### GC content: two defensible answers
#
# The sequence below is **synthetic and exists only for this arithmetic** — it is
# not part of the dataset and nothing about it is a biological claim. It contains
# four `N` bases on purpose, because that is where the two conventions diverge:
# dividing by all residues, or only by the unambiguous ones.

# %%
synthetic = "GGCCNNNN"          # synthetic, for arithmetic only
print("sequence:", synthetic, f"({len(synthetic)} bases)")
print(f"GC / unambiguous ACGT : {gc_content(synthetic):.3f}")
print(f"GC / all residues     : {gc_content(synthetic, denominator='all'):.3f}")
print("GC skew               :", gc_skew("GGGGCC"), "( (G-C)/(G+C) = (4-2)/6 )")

# %% [markdown]
# Both are correct; they answer different questions. A paper that reports "50% GC"
# for this sequence without saying which denominator it used has told you almost
# nothing. The package therefore forces the choice to be explicit in the code.

# %% [markdown]
# ## 3. Quality control on data with known defects
#
# `qc_problems.fasta` is real cytochrome c data with seven defects planted in it,
# each listed in `datasets/metadata/qc_problems.yml`. This is the honest way to
# test a checker: you know the right answer before you run it, and the metadata
# is the answer key.

# %%
damaged = read_fasta(SAMPLE / "qc_problems.fasta")
issues = check_records(damaged)

print(f"{len(damaged)} records, {len(issues)} issues\n")
print(f"{'severity':<9} {'code':<24} {'record':<28} message")
print("-" * 110)
for issue in issues:
    print(f"{issue.severity:<9} {issue.code:<24} {issue.record_id:<28} {issue.message}")

# %% [markdown]
# Read that table as a reviewer would:
#
# - `duplicate_id` is reported **once**, not twice, even though two records share
#   the identifier — a duplicate is a property of the file, not of one record.
# - `internal_stop` is a *warning*: a stop inside a protein sequence is
#   suspicious but has legitimate explanations (a partial CDS, a deliberate
#   construct, a selenoprotein context).
# - `invalid_character` is an *error*: `1` is not a residue, so any computation
#   over that record is meaningless.
# - `lowercase_sequence` is *info*: the parser upper-cased it, nothing is broken,
#   but you should know the file was hand-edited.
#
# Now the other half of the test — a checker that fires on everything is as
# useless as one that fires on nothing:

# %%
clean = read_fasta(SAMPLE / "uniprot_human_subset.fasta")
clean_issues = check_records(clean)
print(f"{len(clean)} real, undamaged records -> {len(clean_issues)} issues")
print("false-positive rate on clean data:", f"{len(clean_issues) / len(clean):.0%}")

# %% [markdown]
# ## 4. Write the report
#
# One data structure, three renderings: JSON for machines, Markdown for a pull
# request, self-contained HTML for a collaborator. They cannot disagree, because
# they are generated from the same object.

# %%
report = build_report(damaged, source="datasets/sample/qc_problems.fasta")
markdown = to_markdown(report)
print(markdown[:1200])
print("...")
print(f"\nMarkdown report: {len(markdown):,} characters")

# %%
from seqreport import to_html

out = REPO / "notebooks" / "_qc_report.html"
out.write_text(to_html(report), encoding="utf-8")
body = out.read_text(encoding="utf-8")
print(f"wrote {out.name}: {len(body):,} bytes")
print("external resources referenced:", body.count("http://") + body.count("https://"), "(0 = opens offline)")
print("script tags:", body.lower().count("<script"))

# %% [markdown]
# ## 5. What this notebook does *not* prove
#
# - The checks are a fixed rule set, not a review. A file with no issues is a file
#   that passes *these* rules.
# - Molecular weight is the average mass of a bare linear peptide. Real proteins
#   are acetylated, cleaved, disulfide-bonded and modified; a mass that differs
#   from a mass spectrometer by tens of daltons is usually chemistry, not a bug.
# - `guess_molecule_type` is a heuristic and is wrong in both directions; it is
#   documented, tested against its known failure, and never used to make a
#   decision that cannot be overridden.
#
# ## Exercises
#
# 1. Change `min_length` to 55 and re-run section 3. Which record changes status,
#    and is the new verdict more or less useful?
# 2. Add a check for "sequence length is a multiple of three" and decide whether
#    it should be an error or a warning for a generic protein file. Justify it.
# 3. Compute the mass of every record in the subset and plot length against mass.
#    Where does the relationship break, and why?
# 4. `record.accession` returns the middle field of a `db|acc|name` identifier.
#    Write a variant that also handles PDB-style `pdb|1ABC|A` headers, and a test
#    that fails on a two-field identifier.
