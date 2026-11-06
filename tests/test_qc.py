"""Tests for the quality checks.

Each test names the defect it plants. If a check is ever removed or inverted,
the test for it fails with a message that says which real-world failure it was
protecting against.
"""

from __future__ import annotations

import io

import pytest
from seqreport.records import parse_fasta

from seqreport.qc import (
    FILE_LEVEL_CODES,
    SEVERITY_ORDER,
    CheckOptions,
    Issue,
    check_records,
    summarise,
)
from seqreport.records import Record

LONG_PROTEIN = "MEEPQSDPSVEPPLSQETFSDLWKLLPENNVLSPLPSQAMDDLMLSPDDIEQWFTEDPGP"
LONG_DNA = "ACGT" * 10


def codes(issues: list[Issue]) -> set[str]:
    return {i.code for i in issues}


class TestIssue:
    def test_bad_severity_is_rejected_at_construction(self):
        with pytest.raises(ValueError, match="severity"):
            Issue(code="x", severity="catastrophe", record_id="a", message="m")

    def test_as_dict_round_trip(self):
        i = Issue("short_sequence", "warning", "a", "too short")
        assert i.as_dict() == {
            "code": "short_sequence",
            "severity": "warning",
            "record_id": "a",
            "message": "too short",
        }


class TestPerRecordChecks:
    def test_clean_record_has_no_issues(self):
        rec = Record(id="ok", description="fine", sequence=LONG_PROTEIN)
        assert check_records([rec]) == []

    def test_empty_sequence_is_an_error(self):
        rec = Record(id="empty", description="d", sequence="")
        assert codes(check_records([rec])) == {"empty_sequence"}
        assert check_records([rec])[0].severity == "error"

    def test_empty_sequence_can_be_allowed(self):
        rec = Record(id="empty", description="d", sequence="")
        opts = CheckOptions(allow_empty_sequence=True)
        assert check_records([rec], opts) == []

    def test_internal_stop_is_a_warning(self):
        seq = LONG_PROTEIN[:20] + "*" + LONG_PROTEIN[21:]
        rec = Record(id="stop", description="d", sequence=seq)
        issues = check_records([rec])
        assert "internal_stop" in codes(issues)
        assert all(i.severity == "warning" for i in issues)

    def test_terminal_stop_is_not_an_internal_stop(self):
        rec = Record(id="okstop", description="d", sequence=LONG_PROTEIN + "-" + "*")
        assert "internal_stop" not in codes(check_records([rec]))

    def test_invalid_protein_character_is_an_error(self):
        seq = LONG_PROTEIN[:10] + "1" + LONG_PROTEIN[11:]
        rec = Record(id="bad", description="d", sequence=seq)
        issues = check_records([rec], CheckOptions(molecule_type="protein"))
        assert "invalid_character" in codes(issues)

    def test_invalid_nucleotide_character_is_an_error(self):
        seq = LONG_DNA[:10] + "E" + LONG_DNA[11:]
        rec = Record(id="bad", description="d", sequence=seq)
        issues = check_records([rec], CheckOptions(molecule_type="nucleotide"))
        assert "invalid_character" in codes(issues)

    def test_short_sequence_is_a_warning(self):
        rec = Record(id="short", description="d", sequence="MEEP")
        assert "short_sequence" in codes(check_records([rec]))

    def test_min_length_option_is_respected(self):
        rec = Record(id="short", description="d", sequence="MEEP")
        assert check_records([rec], CheckOptions(min_length=3)) == []

    def test_lowercase_is_info_only(self):
        # Build the record through the parser, as a learner would: the parser
        # upper-cases `sequence` and keeps `raw_sequence` in the original case,
        # which is exactly the difference the check looks for.
        rec = list(parse_fasta(io.StringIO(f">lc d\n{LONG_PROTEIN.lower()}\n")))[0]
        issues = check_records([rec])
        assert codes(issues) == {"lowercase_sequence"}
        assert issues[0].severity == "info"

    def test_embedded_whitespace_is_a_warning(self):
        raw = LONG_PROTEIN[:20] + "  " + LONG_PROTEIN[20:]
        rec = Record(id="ws", description="d", sequence=LONG_PROTEIN, raw_sequence=raw)
        issues = check_records([rec])
        assert "whitespace_in_sequence" in codes(issues)
        assert {i.severity for i in issues if i.code == "whitespace_in_sequence"} == {"warning"}

    def test_high_ambiguity_is_a_warning(self):
        seq = "".join("X" if i % 4 == 3 else c for i, c in enumerate(LONG_PROTEIN))
        rec = Record(id="amb", description="d", sequence=seq)
        assert "high_ambiguity" in codes(check_records([rec]))

    def test_ambiguity_threshold_is_configurable(self):
        seq = "".join("X" if i % 10 == 9 else c for i, c in enumerate(LONG_PROTEIN))
        rec = Record(id="amb", description="d", sequence=seq)
        strict = check_records([rec], CheckOptions(max_ambiguous_fraction=0.05))
        loose = check_records([rec], CheckOptions(max_ambiguous_fraction=0.5))
        assert "high_ambiguity" in codes(strict)
        assert "high_ambiguity" not in codes(loose)

    def test_selenocysteine_is_info_not_error(self):
        seq = LONG_PROTEIN[:20] + "U" + LONG_PROTEIN[21:]
        rec = Record(id="sec", description="d", sequence=seq)
        issues = check_records([rec], CheckOptions(molecule_type="protein"))
        assert "rare_residue" in codes(issues)
        assert "invalid_character" not in codes(issues)

    def test_bare_header_is_info(self):
        rec = Record(id="bare", description="", sequence=LONG_PROTEIN)
        assert codes(check_records([rec])) == {"bare_header"}


class TestFileLevelChecks:
    def test_duplicate_identifier_is_an_error_reported_once(self):
        rec = Record(id="dup", description="d", sequence=LONG_PROTEIN)
        issues = check_records([rec, rec])
        dupes = [i for i in issues if i.code == "duplicate_id"]
        assert len(dupes) == 1
        assert dupes[0].severity == "error"
        assert dupes[0].code in FILE_LEVEL_CODES

    def test_duplicates_can_be_allowed(self):
        rec = Record(id="dup", description="d", sequence=LONG_PROTEIN)
        opts = CheckOptions(allow_duplicate_ids=True)
        assert check_records([rec, rec], opts) == []

    def test_different_identifiers_are_not_duplicates(self):
        a = Record(id="a", description="d", sequence=LONG_PROTEIN)
        b = Record(id="b", description="d", sequence=LONG_PROTEIN)
        assert "duplicate_id" not in codes(check_records([a, b]))


class TestOrderingAndAggregation:
    def test_errors_come_before_warnings_before_info(self):
        records = [
            Record(id="c", description="", sequence=LONG_PROTEIN),               # info
            Record(id="b", description="d", sequence="MEEP"),                    # warning
            Record(id="a", description="d", sequence=""),                        # error
        ]
        issues = check_records(records)
        severities = [i.severity for i in issues]
        assert severities == sorted(severities, key=lambda s: SEVERITY_ORDER[s])

    def test_summary_counts(self):
        records = [
            Record(id="a", description="d", sequence=""),
            Record(id="b", description="d", sequence="MEEP"),
            Record(id="c", description="d", sequence=LONG_PROTEIN),
        ]
        issues = check_records(records)
        summary = summarise(records, issues)
        assert summary.records == 3
        assert summary.residues == 0 + 4 + len(LONG_PROTEIN)
        assert summary.errors == 1
        assert summary.warnings == 1
        assert summary.clean_records == 1

    def test_summary_of_empty_input(self):
        summary = summarise([], [])
        assert summary.records == 0
        assert summary.molecule_type == "unknown"

    def test_summary_votes_on_molecule_type(self):
        records = [
            Record(id="p1", description="d", sequence=LONG_PROTEIN),
            Record(id="p2", description="d", sequence=LONG_PROTEIN),
            Record(id="n1", description="d", sequence=LONG_DNA),
        ]
        summary = summarise(records, [])
        assert summary.molecule_type == "protein"
        assert summary.molecule_votes["protein"] == 2

    def test_summary_serialises(self):
        summary = summarise([Record(id="a", description="d", sequence=LONG_DNA)], [])
        data = summary.as_dict()
        assert set(data) == {
            "records", "residues", "errors", "warnings", "info",
            "clean_records", "molecule_type", "molecule_votes",
        }

    def test_generator_input_is_accepted(self):
        # check_records must not assume a list: callers stream large files.
        def gen():
            yield Record(id="a", description="d", sequence=LONG_PROTEIN)

        assert check_records(gen()) == []


class TestRealPlantedDataset:
    """The shipped QC dataset must produce exactly the planted defects."""

    def test_every_planted_defect_is_found(self, planted_records):
        issues = check_records(planted_records)
        found = codes(issues)
        expected = {
            "duplicate_id",
            "internal_stop",
            "invalid_character",
            "lowercase_sequence",
            "whitespace_in_sequence",
            "high_ambiguity",
            "empty_sequence",
        }
        assert found == expected

    def test_no_other_issues_are_invented(self, planted_records):
        # The truncated record is 60 aa, above the 20 aa threshold, so it must
        # NOT be flagged as short; if it ever is, the threshold moved silently.
        issues = check_records(planted_records)
        assert "short_sequence" not in codes(issues)
