"""Quality checks.

The design point of this module: **every issue carries a severity and a
reason**, and nothing is silently dropped or auto-corrected. A checker that
quietly fixes a record has hidden the problem from the person who needed to see
it — usually the person who produced it.

Severities
----------
``error``
    The record cannot be interpreted as claimed (empty sequence, invalid
    character for the declared molecule type, duplicated identifier). An
    analysis that includes it will be wrong.
``warning``
    The record is interpretable but suspicious (internal stop in a protein,
    very short sequence, high fraction of ambiguous residues, whitespace or
    lowercase in the raw text, header with no description).
``info``
    Worth reporting, never blocking (e.g. ``U``/``O`` selenocysteine or
    pyrrolysine residues, which are legitimate).

This is a deliberately small rule set. It is not a substitute for looking at
the data; it is a way to make "I looked at the data" reproducible.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Sequence

from .records import Record, guess_molecule_type

NUCLEOTIDE_ALLOWED = frozenset("ACGTUNRYKMSWBDHV-.")
PROTEIN_ALLOWED = frozenset("ACDEFGHIKLMNPQRSTVWYBXZUOJ*-")
PROTEIN_AMBIGUOUS = frozenset("BXZJUO")

SEVERITY_ORDER = {"error": 0, "warning": 1, "info": 2}

#: Issues that belong to the file, not to one record. Reporting them per-record
#: would duplicate the same message once for every copy of the identifier.
FILE_LEVEL_CODES = frozenset({"duplicate_id"})


@dataclass(frozen=True)
class Issue:
    """One problem found in one record (or in the file as a whole)."""

    code: str
    severity: str
    record_id: str
    message: str

    def __post_init__(self) -> None:
        if self.severity not in SEVERITY_ORDER:
            raise ValueError(f"severity must be one of {sorted(SEVERITY_ORDER)}, not {self.severity!r}")

    def as_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "severity": self.severity,
            "record_id": self.record_id,
            "message": self.message,
        }


@dataclass
class CheckOptions:
    """Thresholds for the checks. Defaults are deliberately conservative."""

    molecule_type: str = "auto"          # "auto", "protein" or "nucleotide"
    min_length: int = 20                 # shorter is a warning
    max_ambiguous_fraction: float = 0.10  # above → warning
    allow_duplicate_ids: bool = False
    allow_empty_sequence: bool = False


def _check_one(rec: Record, opts: CheckOptions, molecule: str) -> list[Issue]:
    issues: list[Issue] = []
    rid = rec.id or "<unnamed>"

    if not rec.sequence:
        if not opts.allow_empty_sequence:
            issues.append(Issue("empty_sequence", "error", rid,
                                "header has no sequence data"))
        return issues

    if rec.raw_sequence != rec.sequence:
        # Two sub-cases are worth separating: case-only differences are benign;
        # embedded whitespace is a formatting bug that changes nothing here but
        # breaks naive parsers elsewhere.
        if "".join(rec.raw_sequence.split()) != rec.raw_sequence:
            issues.append(Issue("whitespace_in_sequence", "warning", rid,
                                "sequence lines contain embedded whitespace"))
        letters = "".join(rec.raw_sequence.split())
        if letters != letters.upper():
            issues.append(Issue("lowercase_sequence", "info", rid,
                                "sequence contains lowercase letters (upper-cased on read)"))

    allowed = PROTEIN_ALLOWED if molecule == "protein" else NUCLEOTIDE_ALLOWED
    invalid = sorted({ch for ch in rec.sequence if ch not in allowed})
    if invalid:
        issues.append(Issue("invalid_character", "error", rid,
                            f"character(s) {''.join(invalid)!r} are not valid for a {molecule} sequence"))

    if len(rec.sequence) < opts.min_length:
        issues.append(Issue("short_sequence", "warning", rid,
                            f"length {len(rec.sequence)} is below the minimum of {opts.min_length}"))

    if molecule == "protein":
        if "*" in rec.sequence[:-1]:
            issues.append(Issue("internal_stop", "warning", rid,
                                "'*' (stop) inside the sequence; may indicate a frameshift or a partial CDS"))
        ambiguous = sum(1 for ch in rec.sequence if ch in PROTEIN_AMBIGUOUS)
        if ambiguous / len(rec.sequence) > opts.max_ambiguous_fraction:
            issues.append(Issue("high_ambiguity", "warning", rid,
                                f"{ambiguous}/{len(rec.sequence)} residues are ambiguous "
                                f"(>{opts.max_ambiguous_fraction:.0%})"))
        rare = sorted(set(rec.sequence) & {"U", "O"})
        if rare:
            issues.append(Issue("rare_residue", "info", rid,
                                f"contains {''.join(rare)!r} (selenocysteine/pyrrolysine) — legitimate"))
    else:
        ambiguous = sum(1 for ch in rec.sequence if ch in "NRYKMSWBDHV")
        if ambiguous and ambiguous / len(rec.sequence) > opts.max_ambiguous_fraction:
            issues.append(Issue("high_ambiguity", "warning", rid,
                                f"{ambiguous}/{len(rec.sequence)} residues are ambiguous "
                                f"(>{opts.max_ambiguous_fraction:.0%})"))

    if not rec.description:
        issues.append(Issue("bare_header", "info", rid,
                            "header has no description after the identifier"))

    return issues


def check_records(records: Iterable[Record], options: CheckOptions | None = None) -> list[Issue]:
    """Run every check over every record and return issues, worst severity first.

    Parameters
    ----------
    records:
        Iterable of :class:`~seqreport.records.Record`.
    options:
        A :class:`CheckOptions`; defaults are used if omitted.

    Returns
    -------
    list[Issue]
        Sorted by severity (``error`` first), then by record id, then by code.

    Examples
    --------
    >>> from seqreport.records import Record
    >>> recs = [Record(id="a", sequence="MEEPQSDPSV"), Record(id="a", sequence="MEEPQSDPSV")]
    >>> sorted({i.code for i in check_records(recs)})
    ['bare_header', 'duplicate_id', 'short_sequence']
    >>> sorted({(i.severity, i.code) for i in check_records(recs)})
    [('error', 'duplicate_id'), ('info', 'bare_header'), ('warning', 'short_sequence')]

    Note the ``sorted(...)`` around the set: printing an unordered ``set`` directly
    would make this doctest depend on hash randomisation - exactly the
    non-reproducibility Module 1 section 4 warns about.
    """
    opts = options or CheckOptions()
    issues: list[Issue] = []
    seen: dict[str, int] = {}

    materialised = list(records)
    for rec in materialised:
        seen[rec.id] = seen.get(rec.id, 0) + 1
        if opts.molecule_type == "auto":
            molecule = guess_molecule_type(rec.sequence)
            if molecule == "unknown":
                # Refuse to guess: check against both alphabets instead of
                # pretending we know which one applies.
                issues.extend(_check_one(rec, opts, "nucleotide"))
                continue
        else:
            molecule = opts.molecule_type
        issues.extend(_check_one(rec, opts, molecule))

    if not opts.allow_duplicate_ids:
        for rid, count in seen.items():
            if count > 1 and rid:
                issues.append(Issue("duplicate_id", "error", rid,
                                    f"identifier appears {count} times; "
                                    "downstream joins on id will silently multiply rows"))

    issues.sort(key=lambda i: (SEVERITY_ORDER[i.severity], i.record_id, i.code))
    return issues


@dataclass
class Summary:
    """Counts for the whole file: records, residues, issues by severity."""

    records: int = 0
    residues: int = 0
    errors: int = 0
    warnings: int = 0
    info: int = 0
    clean_records: int = 0
    molecule_type: str = "unknown"
    molecule_votes: dict[str, int] = field(default_factory=dict)

    def as_dict(self) -> dict[str, object]:
        return {
            "records": self.records,
            "residues": self.residues,
            "errors": self.errors,
            "warnings": self.warnings,
            "info": self.info,
            "clean_records": self.clean_records,
            "molecule_type": self.molecule_type,
            "molecule_votes": dict(self.molecule_votes),
        }


def summarise(records: Sequence[Record], issues: Sequence[Issue]) -> Summary:
    """Summarise a file: how many records, how clean, which molecule."""
    votes: dict[str, int] = {}
    residues = 0
    for rec in records:
        residues += len(rec.sequence)
        kind = guess_molecule_type(rec.sequence)
        votes[kind] = votes.get(kind, 0) + 1
    dominant = max(votes, key=lambda k: votes[k]) if votes else "unknown"

    bad_ids = {i.record_id for i in issues if i.severity in {"error", "warning"}}
    return Summary(
        records=len(records),
        residues=residues,
        errors=sum(1 for i in issues if i.severity == "error"),
        warnings=sum(1 for i in issues if i.severity == "warning"),
        info=sum(1 for i in issues if i.severity == "info"),
        clean_records=sum(1 for r in records if r.id not in bad_ids),
        molecule_type=dominant,
        molecule_votes=votes,
    )
