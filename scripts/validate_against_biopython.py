#!/usr/bin/env python3
"""Cross-validate seqreport against Biopython.

Our own tests prove the code agrees with itself and with hand arithmetic. This
script proves something different and stronger: that the numbers agree with an
independent, widely-used implementation (Biopython), on the data we ship.

What is compared
----------------
1. **Parsing.** Every record of every committed dataset: identifier and sequence
   must be identical to what ``Bio.SeqIO.parse`` returns. 76 records.
2. **Molecular weight.** Every protein record, against
   ``Bio.SeqUtils.molecular_weight(..., "protein")`` (average masses).
3. **GC content.** 200 deterministic pseudo-random DNA sequences, against
   ``Bio.SeqUtils.gc_fraction(..., ambiguous="remove")``.
4. **Ambiguity handling.** Our default *refuses* to compute a mass when a residue
   has no tabulated mass; Biopython raises too. Both behaviours are checked, so
   the agreement is on the refusal, not just on the happy path.

Where we deliberately differ
----------------------------
* Biopython's ``molecular_weight`` raises on any unknown letter, including
  ``X``/``B``/``Z``. We raise by default as well (so we agree), but allow
  ``strict=False`` to skip them; the reporter uses that and lists the residues
  separately. The validation asserts the strict paths agree.
* GC: Biopython's default counts ambiguous bases differently. We compare against
  the explicitly-matched mode only, and say so here rather than tuning until the
  numbers happen to match.
* An **empty sequence**: Biopython's protein mass returns ~18.0 Da (it subtracts
  minus-one waters), we refuse. A zero-length molecule has no mass, so this is a
  disagreement we keep, and the script checks that both refuse the same real
  errors while allowing this documented divergence.

Exit code 0 = every comparison agreed.

    python scripts/validate_against_biopython.py
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from seqreport.composition import gc_content, molecular_weight  # noqa: E402
from seqreport.records import read_fasta  # noqa: E402

try:
    from Bio import SeqIO
    from Bio.SeqUtils import gc_fraction, molecular_weight as bio_mass
except ImportError:  # pragma: no cover
    print("error: Biopython is required for cross-validation: pip install biopython", file=sys.stderr)
    raise SystemExit(2)

SAMPLE = REPO / "datasets" / "sample"
TOLERANCE_DA = 1e-6     # both use the same table and water mass


def check_parsing() -> tuple[int, int]:
    checked = failed = 0
    for path in sorted(SAMPLE.glob("*.fasta")):
        ours = read_fasta(path)
        theirs = list(SeqIO.parse(str(path), "fasta"))
        if len(ours) != len(theirs):
            print(f"FAIL {path.name}: {len(ours)} records vs Biopython's {len(theirs)}")
            failed += 1
            continue
        for a, b in zip(ours, theirs):
            checked += 1
            if a.id != b.id or a.sequence != str(b.seq).upper():
                print(f"FAIL {path.name}: record {a.id!r} differs from Biopython's {b.id!r}")
                failed += 1
    return checked, failed


def check_mass() -> tuple[int, int]:
    """Compare masses on every record that has one, and refusals where neither can."""
    checked = failed = 0
    standard = set("ACDEFGHIKLMNPQRSTVWY")
    for path in sorted(SAMPLE.glob("*.fasta")):
        for rec in read_fasta(path):
            seq = rec.sequence
            if not seq:
                # Deliberate difference: Biopython returns ~18.0 Da for an empty
                # sequence (it subtracts -1 waters); we refuse, because an empty
                # sequence has no mass. Counted in check_refusals, not here.
                continue
            if set(seq) <= standard:
                checked += 1
                ours = molecular_weight(seq)
                theirs = bio_mass(seq, "protein")
                if abs(ours - theirs) > TOLERANCE_DA:
                    print(f"FAIL {rec.id}: {ours:.6f} Da vs Biopython's {theirs:.6f} Da")
                    failed += 1
                continue
            # Contains something outside the 20 standard residues: both
            # implementations must refuse, or both must cope.
            try:
                theirs = bio_mass(seq, "protein")
            except (ValueError, KeyError):
                checked += 1
                try:
                    molecular_weight(seq)
                except ValueError:
                    continue
                print(f"FAIL {rec.id}: Biopython refused but we returned a value")
                failed += 1
            else:
                checked += 1
                try:
                    ours = molecular_weight(seq)
                except ValueError:
                    print(f"FAIL {rec.id}: Biopython computed {theirs:.3f} Da but we refused")
                    failed += 1
    return checked, failed


def check_gc(n: int = 200, seed: int = 20261106) -> tuple[int, int]:
    rng = random.Random(seed)     # seeded: the same 200 sequences every run
    checked = failed = 0
    for _ in range(n):
        seq = "".join(rng.choice("ACGT") for _ in range(rng.randint(20, 400)))
        theirs = gc_fraction(seq, ambiguous="remove")
        ours = gc_content(seq)
        checked += 1
        if abs(ours - theirs) > 1e-12:
            print(f"FAIL GC on {seq[:20]}…: {ours!r} vs Biopython's {theirs!r}")
            failed += 1
    return checked, failed


def check_refusals() -> tuple[int, int]:
    checked = failed = 0
    for seq in ("MEEPX", "MEEP*", "MEEP1", "MEEP-"):
        checked += 1
        bio_ok = False
        try:
            bio_mass(seq, "protein")
        except (ValueError, KeyError):
            bio_ok = True
        ours_ok = False
        try:
            molecular_weight(seq)
        except ValueError:
            ours_ok = True
        if bio_ok != ours_ok:
            print(f"FAIL refusal mismatch on {seq!r}: biopython_refused={bio_ok}, we_refused={ours_ok}")
            failed += 1
    return checked, failed


def check_documented_divergence() -> tuple[int, int]:
    """The one place we deliberately disagree, asserted in the direction we claim."""
    checked, failed = 0, 0
    checked += 1
    bio_value = bio_mass("", "protein")          # Biopython: 18.0153...
    try:
        molecular_weight("")
    except ValueError:
        if abs(bio_value - 18.0153) < 1e-3:
            print(f"note: empty sequence — Biopython returns {bio_value:.4f} Da, we refuse (documented)")
        else:
            print(f"FAIL empty sequence: unexpected Biopython value {bio_value}")
            failed += 1
    else:
        print("FAIL empty sequence: we returned a mass; the documented behaviour is to refuse")
        failed += 1
    return checked, failed


def main() -> int:
    print("Cross-validating seqreport against Biopython", bio_version())
    print("-" * 68)
    sections = [
        ("record parsing (id + sequence)", check_parsing),
        ("molecular weight (Da)", check_mass),
        ("GC content (200 seeded sequences)", check_gc),
        ("refusal on unresolvable residues", check_refusals),
        ("documented divergence (empty sequence)", check_documented_divergence),
    ]
    total_checked = total_failed = 0
    for label, fn in sections:
        checked, failed = fn()
        total_checked += checked
        total_failed += failed
        status = "OK  " if failed == 0 else "FAIL"
        print(f"{status} {label}: {checked - failed}/{checked} agreed")
    print("-" * 68)
    if total_failed:
        print(f"{total_failed} comparison(s) DISAGREED — do not ship this")
        return 1
    print(f"All {total_checked} comparisons agree with Biopython.")
    print("Note: agreement is evidence of correctness, not proof — both")
    print("implementations could share the same wrong convention.")
    return 0


def bio_version() -> str:
    import Bio

    return getattr(Bio, "__version__", "unknown")


if __name__ == "__main__":
    sys.exit(main())
