"""FASTA parsing and writing.

Three decisions worth understanding, because each one is a lesson:

1. **Streaming.** ``parse_fasta`` is a generator. A 3 GB FASTA never has to fit
   in memory: you get one record at a time. ``read_fasta`` materialises the
   list, which is convenient and is the wrong choice for large files — the
   difference is the whole point of module 4.
2. **Two sequence strings per record.** ``sequence`` is upper-cased and
   whitespace-free (what you compute on). ``raw_sequence`` preserves exactly
   what was in the file (what you need in order to notice that a file contains
   lowercase, spaces, or Windows line endings). Analysis uses the first;
   quality control compares the two.
3. **Strictness.** A malformed record raises ``FastaError`` rather than being
   silently repaired. Silent repair is how a truncated download becomes a
   published result.
"""

from __future__ import annotations

import gzip
import io
from dataclasses import dataclass, field
from pathlib import Path
from typing import IO, Iterator, Iterable


class FastaError(ValueError):
    """Raised when a file is not valid FASTA."""


@dataclass(frozen=True)
class Record:
    """One FASTA record.

    Attributes
    ----------
    id:
        First whitespace-delimited token of the header (e.g. ``P99999``).
    description:
        The rest of the header, or ``""`` if there is nothing after the id.
    sequence:
        Upper-cased sequence with all whitespace removed.
    raw_sequence:
        Sequence exactly as it appeared between the header lines, including
        case, whitespace and any internal newlines removed but otherwise
        untouched.
    """

    id: str
    description: str = ""
    sequence: str = ""
    raw_sequence: str = ""
    line_number: int = field(default=0, compare=False)

    def __len__(self) -> int:
        return len(self.sequence)

    @property
    def header(self) -> str:
        return f"{self.id} {self.description}".strip()

    @property
    def accession(self) -> str:
        """Database accession, when the id is a UniProt-style ``db|acc|name``.

        FASTA's identifier is only "the first token of the header". UniProt packs
        three fields into that token, so the accession is the middle one — this
        property exists because every learner hits that surprise once, and
        splitting on ``|`` by hand in five different scripts is how databases end
        up silently mixed.

        >>> Record(id="sp|P99999|CYC_HUMAN").accession
        'P99999'
        >>> Record(id="contig_1").accession
        'contig_1'
        """
        parts = self.id.split("|")
        return parts[1] if len(parts) == 3 else self.id

    def to_fasta(self, width: int = 60) -> str:
        """Return this record as FASTA text, wrapped at ``width`` characters."""
        if width < 1:
            raise ValueError("width must be at least 1")
        body = "\n".join(self.sequence[i : i + width] for i in range(0, len(self.sequence), width))
        return f">{self.header}\n{body}\n" if body else f">{self.header}\n"


def _open_maybe_gzip(path: Path | str) -> IO[str]:
    p = Path(path)
    if not p.exists():
        raise FastaError(f"no such file: {p}")
    if p.suffix in {".gz", ".gzip"}:
        return io.TextIOWrapper(gzip.open(p, "rb"), encoding="utf-8")
    return p.open("r", encoding="utf-8")


def parse_fasta(source: Path | str | IO[str]) -> Iterator[Record]:
    """Yield :class:`Record` objects from a FASTA file, path or text stream.

    Parameters
    ----------
    source:
        A path (``str`` or :class:`~pathlib.Path`), a file object, or a
        :class:`io.StringIO` holding FASTA text.

    Yields
    ------
    Record

    Raises
    ------
    FastaError
        If a sequence appears before the first header, if a header is empty,
        or if the source does not exist.

    Examples
    --------
    >>> import io
    >>> recs = list(parse_fasta(io.StringIO(">a one\\nACGT\\n>b\\nGGCC\\n")))
    >>> [r.id for r in recs]
    ['a', 'b']
    >>> recs[0].sequence
    'ACGT'
    """
    close_after = False
    handle: IO[str]
    if isinstance(source, (str, Path)):
        handle = _open_maybe_gzip(source)
        close_after = True
    else:
        handle = source

    try:
        header: str | None = None
        line_number = 0
        parts: list[str] = []
        record_start = 0
        for raw_line in handle:
            line_number += 1
            line = raw_line.rstrip("\r\n")
            if not line.strip():
                continue  # blank lines between records are tolerated
            if line.startswith(">"):
                if header is not None:
                    yield _build(header, parts, record_start)
                header = line[1:].strip()
                record_start = line_number
                parts = []
                if not header:
                    raise FastaError(f"line {line_number}: empty FASTA header ('>' with no identifier)")
                continue
            if header is None:
                raise FastaError(
                    f"line {line_number}: sequence data before the first '>' header. "
                    "This is not a FASTA file."
                )
            parts.append(line)
        if header is not None:
            yield _build(header, parts, record_start)
    finally:
        if close_after:
            handle.close()


def _build(header: str, parts: list[str], record_start: int) -> Record:
    head_id, _, description = header.partition(" ")
    raw = "".join(parts)
    sequence = "".join(raw.split()).upper()
    return Record(
        id=head_id,
        description=description.strip(),
        sequence=sequence,
        raw_sequence=raw,
        line_number=record_start,
    )


def read_fasta(source: Path | str | IO[str]) -> list[Record]:
    """Materialise every record into a list.

    Convenient for small files; do not use it on a file you have not measured.
    Use :func:`parse_fasta` to stream instead.
    """
    return list(parse_fasta(source))


def write_fasta(records: Iterable[Record], target: Path | str | IO[str], width: int = 60) -> None:
    """Write records to a path (``.gz`` compresses) or an open text stream."""
    close_after = False
    if isinstance(target, (str, Path)):
        p = Path(target)
        p.parent.mkdir(parents=True, exist_ok=True)
        if p.suffix in {".gz", ".gzip"}:
            handle: IO[str] = io.TextIOWrapper(gzip.open(p, "wb"), encoding="utf-8")
        else:
            handle = p.open("w", encoding="utf-8")
        close_after = True
    else:
        handle = target
    try:
        for rec in records:
            handle.write(rec.to_fasta(width=width))
    finally:
        if close_after:
            handle.close()


_NUCLEOTIDE_ALPHABET = set("ACGTUNRYKMSWBDHV")
_PROTEIN_ONLY = set("EFILPQZJOX*")


def guess_molecule_type(sequence: str) -> str:
    """Guess ``"nucleotide"`` or ``"protein"`` from composition.

    This is a heuristic and it is wrong in both directions:

    * a short protein made only of ``A``, ``C``, ``G`` and ``T`` residues
      (there are real ones — ``ACGT``-rich peptides exist) looks like DNA;
    * a nucleotide sequence containing ``N``, ``R`` or ``Y`` ambiguity codes
      could look protein-like if it also happens to contain no other tell.

    The rule used here: if the sequence contains any residue that cannot appear
    in a nucleic acid (``E``, ``F``, ``I``, ``L``, ``P``, ``Q``, ``Z``, ``J``,
    ``O``, ``X`` or ``*``) it is a protein; otherwise, if it is at least 20
    residues and more than 90% of the residues are unambiguous nucleotides, it
    is called a nucleotide. Everything else returns ``"unknown"`` — an honest
    answer beats a confident wrong one, which is the module's recurring theme.

    Examples
    --------
    >>> guess_molecule_type("ACGTACGTACGTACGTACGT")
    'nucleotide'
    >>> guess_molecule_type("MGDVEKGKKIFIMK")
    'protein'
    >>> guess_molecule_type("ACG")
    'unknown'
    """
    seq = "".join(sequence.split()).upper()
    if not seq:
        return "unknown"
    if _PROTEIN_ONLY & set(seq):
        return "protein"
    unambiguous = sum(1 for ch in seq if ch in "ACGTU")
    if len(seq) >= 20 and unambiguous / len(seq) > 0.9:
        return "nucleotide"
    if set(seq) <= set("ACGTU"):
        return "nucleotide" if len(seq) >= 20 else "unknown"
    return "protein" if len(seq) > 20 else "unknown"
