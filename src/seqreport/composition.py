"""Composition statistics, worked out from the sequence rather than imported.

Every function here is a few lines of ordinary Python on purpose: the learner
should be able to check the arithmetic by hand and then check it again against
Biopython (see ``docs/validation.md``).

Biological caution that the lessons keep returning to:

* **GC content has several defensible denominators** (all residues, or only
  unambiguous A/C/G/T). They differ most for sequences with many ``N``. This
  module always reports which denominator it used.
* **Skew is undefined when its denominator is zero** — a sequence with no G and
  no C has no GC skew. Returning ``0.0`` would be a lie; returning ``None``
  forces the caller to decide.
* **Molecular weight is a property of the molecule, not of the sequence
  string.** The value below is the average mass of a linear peptide with free
  termini: the sum of the residue (free amino acid) masses minus one water per
  peptide bond. Disulfide bonds, N-terminal acetylation, formylation and
  pyroglutamate formation all change the real mass, so a value that disagrees
  with a mass spectrometer by tens of daltons is usually not a bug in the code.
"""

from __future__ import annotations

from collections import Counter
from typing import Iterable

#: Average masses of the free amino acids in daltons (IUPAC values, as tabulated
#: in Expasy ProtParam and in Biopython's ``Bio.Data.IUPACData.protein_weights``).
RESIDUE_MASSES: dict[str, float] = {
    "A": 89.0932, "C": 121.1582, "D": 133.1027, "E": 147.1293, "F": 165.1891,
    "G": 75.0666, "H": 155.1546, "I": 131.1729, "K": 146.1876, "L": 131.1729,
    "M": 149.2113, "N": 132.1179, "O": 255.3134, "P": 115.1305, "Q": 146.1445,
    "R": 174.2010, "S": 105.0926, "T": 119.1192, "U": 168.0532, "V": 117.1463,
    "W": 204.2252, "Y": 181.1885,
}
#: Average mass of water, lost once per peptide bond.
WATER = 18.0153
#: Residues with no single-residue mass in the table above.
AMBIGUOUS_WITHOUT_MASS = frozenset("BJXZ*")

DNA_LETTERS = frozenset("ACGT")
RNA_LETTERS = frozenset("ACGU")
NUCLEOTIDE_AMBIGUOUS = frozenset("NRYKMSWBDHV")


def composition(sequence: str, *, include_ambiguous: bool = True) -> dict[str, int]:
    """Count residues, most common first.

    >>> composition("ACGTACGTNN")
    {'A': 2, 'C': 2, 'G': 2, 'N': 2, 'T': 2}
    """
    seq = "".join(sequence.split()).upper()
    counts = Counter(seq)
    if not include_ambiguous:
        counts = Counter({k: v for k, v in counts.items() if k in DNA_LETTERS | RNA_LETTERS})
    return dict(sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])))


def gc_content(sequence: str, *, denominator: str = "acgt") -> float:
    """GC fraction, in ``[0, 1]``.

    Parameters
    ----------
    sequence:
        Nucleotide sequence; case and whitespace insensitive.
    denominator:
        ``"acgt"`` (default) divides by the number of unambiguous A/C/G/T/U
        residues — the usual convention, which ignores ``N`` and ambiguity
        codes. ``"all"`` divides by every residue, so ``N`` counts as
        non-GC. Report which one you used; they are different numbers.

    Raises
    ------
    ValueError
        If ``denominator`` is not one of the two options, or if the chosen
        denominator is zero (empty sequence, or a sequence of only ``N``).

    Examples
    --------
    >>> round(gc_content("GGGCCCATA"), 4)
    0.6667
    >>> round(gc_content("GGGCCCATA", denominator="all"), 4)
    0.6667
    >>> round(gc_content("GGCCNNNN"), 4)
    1.0
    >>> round(gc_content("GGCCNNNN", denominator="all"), 4)
    0.5
    """
    seq = "".join(sequence.split()).upper()
    gc = sum(1 for ch in seq if ch in "GCS")
    if denominator == "acgt":
        total = sum(1 for ch in seq if ch in "ACGTU")
    elif denominator == "all":
        total = len(seq)
    else:
        raise ValueError(f"denominator must be 'acgt' or 'all', not {denominator!r}")
    if total == 0:
        raise ValueError("GC content is undefined for this sequence (empty denominator)")
    return gc / total


def _skew(a: int, b: int) -> float | None:
    return None if a + b == 0 else (a - b) / (a + b)


def gc_skew(sequence: str) -> float | None:
    """``(G - C) / (G + C)``, or ``None`` when there are no G and no C.

    Positive skew means the strand is G-rich relative to C. Replication origin
    and terminus can often be spotted as sign changes in a windowed plot — which
    is exactly what figure 2 shows, and about as far as a skew plot can take you.

    >>> gc_skew("GGGCCCAA")
    0.0
    >>> gc_skew("GGGGCCAA")
    0.3333333333333333
    >>> gc_skew("AAAA") is None
    True
    """
    seq = "".join(sequence.split()).upper()
    return _skew(seq.count("G"), seq.count("C"))


def at_skew(sequence: str) -> float | None:
    """``(A - T) / (A + T)``, or ``None`` when there are no A and no T.

    >>> at_skew("AAAATT") is not None
    True
    >>> at_skew("GGGG") is None
    True
    """
    seq = "".join(sequence.split()).upper()
    return _skew(seq.count("A"), seq.count("T") + seq.count("U"))


def molecular_weight(sequence: str, *, strict: bool = True) -> float:
    """Average molecular mass of a linear peptide in daltons.

    Sums the residue masses and subtracts one water (18.0153 Da) per peptide
    bond, i.e. ``n - 1`` waters for ``n`` residues.

    Parameters
    ----------
    sequence:
        Protein sequence. Lowercase is accepted; whitespace is ignored.
    strict:
        If ``True`` (default), raise :class:`ValueError` for any residue without
        a tabulated mass (``B``, ``J``, ``X``, ``Z``, ``*``, and any corrupt
        character such as ``1`` or ``-``) instead of guessing. A guessed mass is
        a fabricated number; ``strict=False`` skips those residues and is used
        only by the reporter, which lists them separately as QC issues.

    Examples
    --------
    >>> round(molecular_weight("A"), 4)
    89.0932
    >>> round(molecular_weight("AA"), 4)
    160.1711
    >>> round(molecular_weight("MA"), 4)
    220.2892
    >>> molecular_weight("AX")
    Traceback (most recent call last):
    ...
    ValueError: no tabulated mass for residue(s) 'X'; pass strict=False to skip them
    """
    seq = "".join(sequence.split()).upper()
    if not seq:
        raise ValueError("molecular weight of an empty sequence is undefined")
    unknown = sorted(set(seq) - set(RESIDUE_MASSES))
    if unknown and strict:
        raise ValueError(
            f"no tabulated mass for residue(s) {''.join(unknown)!r}; "
            "pass strict=False to skip them"
        )
    if unknown:
        # A corrupt record can contain anything at all ('1', '-', '?'), not only
        # the conventional ambiguity codes. Skipping is only safe because the
        # caller asked for it, and QC reports the characters separately.
        seq = "".join(ch for ch in seq if ch in RESIDUE_MASSES)
        if not seq:
            raise ValueError("no residues with a tabulated mass remain")
    return sum(RESIDUE_MASSES[ch] for ch in seq) - (len(seq) - 1) * WATER


def kmer_counts(sequence: str, k: int = 3) -> dict[str, int]:
    """Count every overlapping *k*-mer.

    >>> kmer_counts("ACGTAC", 2)
    {'AC': 2, 'CG': 1, 'GT': 1, 'TA': 1}
    >>> kmer_counts("AC", 3)
    {}
    """
    if k < 1:
        raise ValueError("k must be at least 1")
    seq = "".join(sequence.split()).upper()
    counts: Counter[str] = Counter(seq[i : i + k] for i in range(len(seq) - k + 1))
    return dict(sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])))


def windowed_gc(sequence: str, window: int = 50, step: int | None = None,
                *, denominator: str = "acgt") -> list[dict[str, float | int | None]]:
    """GC content in sliding windows.

    Returns a list of dicts with ``start``, ``end`` (0-based, half-open),
    ``gc`` and ``complete``. Two traps are surfaced rather than hidden:

    * the **last window is usually partial** (``complete=False``); its GC is
      computed over fewer residues and is not comparable with the others;
    * a window with no unambiguous nucleotide gets ``gc=None`` rather than
      ``0.0`` — a gap is not a GC-poor region.

    Parameters
    ----------
    window:
        Window length in residues; must be positive.
    step:
        Defaults to ``window`` (non-overlapping, which is what you want for a
        summary). ``step=1`` gives a smooth curve for plotting.

    >>> [w["gc"] for w in windowed_gc("GGGGCCCC", window=4)]
    [1.0, 1.0]
    >>> windowed_gc("GGGG", window=8)
    [{'start': 0, 'end': 4, 'gc': 1.0, 'complete': False}]
    """
    if window < 1:
        raise ValueError("window must be at least 1")
    if step is None:
        step = window
    if step < 1:
        raise ValueError("step must be at least 1")
    seq = "".join(sequence.split()).upper()
    out: list[dict[str, float | int | None]] = []
    for start in range(0, max(len(seq), 1), step):
        chunk = seq[start : start + window]
        if not chunk:
            break
        try:
            value = gc_content(chunk, denominator=denominator)
        except ValueError:
            value = None
        out.append({
            "start": start,
            "end": min(start + window, len(seq)),
            "gc": value,
            "complete": len(chunk) == window,
        })
    return out


def shannon_entropy(sequence: str, k: int = 1) -> float:
    """Shannon entropy of the *k*-mer distribution, in bits.

    Low entropy means a repetitive sequence; :func:`kmer_counts` gives the
    counts, this gives one number. Included because it is three lines and it
    makes the "repeat content" discussion quantitative.

    >>> round(shannon_entropy("AAAA"), 4)
    -0.0
    >>> round(shannon_entropy("ACGT"), 4)
    2.0
    """
    import math

    counts = kmer_counts(sequence, k)
    total = sum(counts.values())
    if total == 0:
        raise ValueError("entropy of an empty sequence is undefined")
    return -sum((c / total) * math.log2(c / total) for c in counts.values())
