"""Tests for FASTA parsing and writing.

Expectations are hand-computed and written out in the test, not derived from the
implementation: a test that asks the code what the answer is proves only that the
code is self-consistent.
"""

from __future__ import annotations

import gzip
import io
from pathlib import Path

import pytest

from seqreport.records import (
    FastaError,
    Record,
    guess_molecule_type,
    parse_fasta,
    read_fasta,
    write_fasta,
)

SAMPLE = """>rec1 first record
ACGTACGTAC
GTACGT
>rec2
GGGGCCCCTTTTAAAA
"""


def write(tmp_path: Path, name: str, text: str) -> Path:
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return p


class TestParsing:
    def test_two_records_in_order(self):
        recs = list(parse_fasta(io.StringIO(SAMPLE)))
        assert [r.id for r in recs] == ["rec1", "rec2"]

    def test_multiline_sequence_is_joined(self):
        rec = list(parse_fasta(io.StringIO(SAMPLE)))[0]
        assert rec.sequence == "ACGTACGTACGTACGT"

    def test_identifier_is_first_token_description_is_the_rest(self):
        rec = list(parse_fasta(io.StringIO(SAMPLE)))[0]
        assert rec.id == "rec1"
        assert rec.description == "first record"
        assert rec.header == "rec1 first record"

    def test_record_without_description(self):
        rec = list(parse_fasta(io.StringIO(SAMPLE)))[1]
        assert rec.description == ""
        assert rec.header == "rec2"

    def test_lowercase_is_uppercased_but_raw_is_preserved(self):
        rec = list(parse_fasta(io.StringIO(">x\nacgtACGT\n")))[0]
        assert rec.sequence == "ACGTACGT"        # what you compute on
        assert rec.raw_sequence == "acgtACGT"    # what you inspect

    def test_internal_whitespace_is_removed_from_sequence_only(self):
        rec = list(parse_fasta(io.StringIO(">x\nAC GT\nAC\tGT\n")))[0]
        assert rec.sequence == "ACGTACGT"
        assert rec.raw_sequence == "AC GTAC\tGT"

    def test_blank_lines_are_tolerated(self):
        recs = list(parse_fasta(io.StringIO(">a\nACGT\n\n\n>b\nGGCC\n")))
        assert [r.sequence for r in recs] == ["ACGT", "GGCC"]

    def test_windows_line_endings(self):
        recs = list(parse_fasta(io.StringIO(">a\r\nACGT\r\n")))
        assert recs[0].sequence == "ACGT"

    def test_empty_sequence_record_is_kept_not_dropped(self):
        # Dropping it would hide the problem; QC needs to see it.
        recs = list(parse_fasta(io.StringIO(">a\n>b\nACGT\n")))
        assert len(recs) == 2
        assert recs[0].sequence == ""

    def test_line_number_points_at_the_header(self):
        recs = list(parse_fasta(io.StringIO(">a\nACGT\n>b\nGGCC\n")))
        assert [r.line_number for r in recs] == [1, 3]

    def test_len_is_sequence_length(self):
        rec = list(parse_fasta(io.StringIO(">a\nACGTA\n")))[0]
        assert len(rec) == 5


class TestParseErrors:
    def test_empty_header_raises(self):
        with pytest.raises(FastaError, match="empty FASTA header"):
            list(parse_fasta(io.StringIO(">\nACGT\n")))

    def test_sequence_before_header_raises(self):
        with pytest.raises(FastaError, match="before the first"):
            list(parse_fasta(io.StringIO("ACGT\n>a\nACGT\n")))

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FastaError, match="no such file"):
            list(parse_fasta(tmp_path / "nope.fasta"))

    def test_fasta_error_is_a_value_error(self):
        # Callers that catch ValueError should still work; this is the contract.
        assert issubclass(FastaError, ValueError)


class TestFilesAndCompression:
    def test_read_from_path(self, tmp_path):
        p = write(tmp_path, "a.fasta", SAMPLE)
        assert len(read_fasta(p)) == 2

    def test_gzip_is_transparent(self, tmp_path):
        p = tmp_path / "a.fasta.gz"
        with gzip.open(p, "wt", encoding="utf-8") as fh:
            fh.write(SAMPLE)
        assert [r.id for r in read_fasta(p)] == ["rec1", "rec2"]

    def test_write_then_read_round_trip(self, tmp_path):
        recs = list(parse_fasta(io.StringIO(SAMPLE)))
        out = tmp_path / "out.fasta"
        write_fasta(recs, out)
        again = read_fasta(out)
        assert again == recs

    def test_write_gzip_round_trip(self, tmp_path):
        recs = list(parse_fasta(io.StringIO(SAMPLE)))
        out = tmp_path / "out.fasta.gz"
        write_fasta(recs, out)
        assert read_fasta(out) == recs

    def test_write_wraps_at_requested_width(self, tmp_path):
        out = tmp_path / "out.fasta"
        write_fasta([Record(id="x", sequence="A" * 25)], out, width=10)
        body = out.read_text().splitlines()[1:]
        assert [len(line) for line in body] == [10, 10, 5]

    def test_write_rejects_bad_width(self):
        with pytest.raises(ValueError, match="width"):
            Record(id="x", sequence="AC").to_fasta(width=0)

    def test_streaming_and_materialised_agree(self, tmp_path):
        p = write(tmp_path, "a.fasta", SAMPLE)
        assert list(parse_fasta(p)) == read_fasta(p)


class TestAccession:
    def test_uniprot_style_header(self):
        assert Record(id="sp|P99999|CYC_HUMAN").accession == "P99999"

    def test_plain_identifier_is_returned_unchanged(self):
        assert Record(id="contig_7").accession == "contig_7"

    def test_two_field_identifier_is_not_guessed(self):
        assert Record(id="a|b").accession == "a|b"


class TestGuessMoleculeType:
    @pytest.mark.parametrize("seq", ["ACGTACGTACGTACGTACGT", "ACGUACGUACGUACGUACGU"])
    def test_nucleotide(self, seq):
        assert guess_molecule_type(seq) == "nucleotide"

    @pytest.mark.parametrize("seq", ["MGDVEKGKKIFIMK", "MEEPQSDPSVEPPLSQETFSDLWKLLPEN"])
    def test_protein(self, seq):
        assert guess_molecule_type(seq) == "protein"

    def test_short_ambiguous_sequence_is_unknown_rather_than_guessed(self):
        assert guess_molecule_type("ACG") == "unknown"

    def test_empty(self):
        assert guess_molecule_type("") == "unknown"

    def test_stop_codon_means_protein(self):
        assert guess_molecule_type("MEEP*") == "protein"

    def test_documented_failure_mode_short_acgt_peptide(self):
        # A real peptide made only of A/C/G/T residues is called nucleotide.
        # The lesson states this limitation; the test pins it so a change of
        # behaviour is a deliberate decision, not a surprise.
        assert guess_molecule_type("ACGTACGTACGTACGTACGT") == "nucleotide"


class TestWritingToStreams:
    def test_write_to_an_open_stream(self):
        out = io.StringIO()
        write_fasta([Record(id="x", sequence="ACGT")], out, width=2)
        assert out.getvalue() == ">x\nAC\nGT\n"

    def test_write_creates_parent_directories(self, tmp_path):
        target = tmp_path / "nested" / "dir" / "out.fasta"
        write_fasta([Record(id="x", sequence="ACGT")], target)
        assert target.is_file()

    def test_write_empty_sequence_record(self, tmp_path):
        target = tmp_path / "empty.fasta"
        write_fasta([Record(id="x", sequence="")], target)
        assert target.read_text() == ">x\n"
