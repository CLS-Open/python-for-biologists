"""Integrity tests for the committed datasets.

These tests are the difference between "we shipped data" and "we shipped data we
can defend". They assert what the metadata claims: the file is the file that was
retrieved, it has the records it says it has, and the derived file contains
exactly the defects it documents — no more, no fewer.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[1]
SAMPLE = REPO / "datasets" / "sample"
META = REPO / "datasets" / "metadata"

ACCESSIONS = ["P99999", "P62897", "P62898", "Q6IQM2", "Q6GQE4", "P84029", "P00044", "P29380"]


def metadata() -> dict[str, dict]:
    return {p.stem: yaml.safe_load(p.read_text(encoding="utf-8")) for p in META.glob("*.yml")}


class TestMetadata:
    def test_every_dataset_has_metadata(self):
        files = {p.stem for p in SAMPLE.glob("*.fasta")}
        assert files == set(metadata())

    def test_metadata_declares_provenance(self):
        for name, meta in metadata().items():
            assert meta["synthetic"] is False, f"{name}: this repository ships real data"
            assert meta.get("source"), f"{name}: no source recorded"
            assert meta.get("license"), f"{name}: no licence recorded"

    def test_recorded_sha256_matches_the_file(self):
        for name, meta in metadata().items():
            path = REPO / meta["file"]
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            assert digest == meta["sha256"], f"{name}: file does not match its recorded hash"

    def test_recorded_record_count_matches_the_file(self):
        for name, meta in metadata().items():
            text = (REPO / meta["file"]).read_text(encoding="utf-8")
            count = sum(1 for line in text.splitlines() if line.startswith(">"))
            assert count == meta["records"], f"{name}: record count is wrong"

    def test_licence_is_cc_by(self):
        for name, meta in metadata().items():
            assert "CC BY" in meta["license"], f"{name}: expected a CC BY licence"

    def test_retrieval_date_is_iso(self):
        for name, meta in metadata().items():
            assert len(str(meta["retrieved"])) == 10
            assert str(meta["retrieved"]).count("-") == 2


class TestUniprotSubset:
    def test_sixty_records(self, uniprot_subset):
        assert len(uniprot_subset) == 60

    def test_all_human(self, uniprot_subset):
        assert all("OS=Homo sapiens" in r.description for r in uniprot_subset)

    def test_all_reviewed_uniprot(self, uniprot_subset):
        assert all(r.id.startswith("sp|") for r in uniprot_subset)

    def test_lengths_within_the_documented_window(self, uniprot_subset):
        lengths = [len(r) for r in uniprot_subset]
        assert min(lengths) >= 100
        assert max(lengths) <= 800

    def test_identifiers_are_unique(self, uniprot_subset):
        ids = [r.id for r in uniprot_subset]
        assert len(ids) == len(set(ids))

    def test_all_sequences_are_protein_letters(self, uniprot_subset):
        allowed = set("ACDEFGHIKLMNPQRSTVWYBXZ*")
        for rec in uniprot_subset:
            assert set(rec.sequence) <= allowed, rec.id

    def test_accession_property_extracts_the_middle_field(self, uniprot_subset):
        assert all(r.accession == r.id.split("|")[1] for r in uniprot_subset)


class TestGeneFamily:
    def test_eight_orthologues(self, cycs_family):
        assert len(cycs_family) == 8

    def test_accessions_are_the_documented_ones(self, cycs_family):
        assert [r.accession for r in cycs_family] == ACCESSIONS

    def test_lengths_are_cytochrome_c_sized(self, cycs_family):
        # Real cytochrome c is ~100-115 residues; anything far outside means the
        # wrong entry was fetched.
        for rec in cycs_family:
            assert 100 <= len(rec) <= 115, f"{rec.accession}: {len(rec)} aa"

    def test_all_named_cytochrome_c(self, cycs_family):
        for rec in cycs_family:
            assert "Cytochrome c" in rec.description, rec.accession

    def test_species_are_distinct(self, cycs_family):
        organisms = [r.description.split("OS=")[1].split(" OX=")[0] for r in cycs_family]
        assert len(set(organisms)) == 8

    def test_they_share_the_haem_attachment_motif(self, cycs_family):
        # Cys-X-X-Cys-His: the haem-binding motif is conserved across all eight.
        import re

        for rec in cycs_family:
            assert re.search(r"C[A-Z]{2}CH", rec.sequence), rec.accession

    def test_human_and_chimp_would_be_nearly_identical_but_we_have_no_chimp(self, cycs_family):
        # Guard against silent accretion of extra records into the family file.
        assert len({r.accession for r in cycs_family}) == 8


class TestPlantedProblems:
    def test_eight_records(self, planted_records):
        assert len(planted_records) == 8

    def test_documented_defects_match_reality(self, planted_records):
        meta = metadata()["qc_problems"]
        documented = {d["id"] for d in meta["planted_defects"]}
        by_alias = {}
        for rec in planted_records:
            alias = rec.id.split("|")[-1]
            by_alias[alias] = rec
        assert documented == set(by_alias)

    def test_duplicate_pair_is_byte_identical(self, planted_records):
        copies = [r for r in planted_records if r.id == "P99999|pl_duplicate"]
        assert len(copies) == 2
        assert copies[0].sequence == copies[1].sequence

    def test_internal_stop_is_exactly_one_and_mid_sequence(self, planted_records):
        rec = next(r for r in planted_records if r.id.endswith("pl_internal_stop"))
        assert rec.sequence.count("*") == 1
        assert 0 < rec.sequence.index("*") < len(rec.sequence) - 1

    def test_invalid_character_is_a_digit_at_position_11(self, planted_records):
        rec = next(r for r in planted_records if r.id.endswith("pl_invalid_residue"))
        assert rec.sequence[10] == "1"

    def test_lowercase_record_is_still_uppercased_on_read(self, planted_records):
        rec = next(r for r in planted_records if r.id.endswith("pl_lowercase_whitespace"))
        assert rec.sequence.isupper()
        assert rec.raw_sequence != rec.sequence

    def test_truncated_record_is_shorter_than_its_source(self, planted_records, cycs_family):
        rec = next(r for r in planted_records if r.id.endswith("pl_truncated"))
        source = next(r for r in cycs_family if r.accession == "Q6GQE4")
        assert len(rec) == 60
        assert len(rec) < len(source)
        assert source.sequence.startswith(rec.sequence)

    def test_ambiguous_record_is_about_a_quarter_x(self, planted_records):
        rec = next(r for r in planted_records if r.id.endswith("pl_ambiguous_rich"))
        assert rec.sequence.count("X") == 27

    def test_empty_record_has_a_header_and_nothing_else(self, planted_records):
        rec = next(r for r in planted_records if r.id == "pl_empty_record")
        assert rec.sequence == ""
        assert rec.description


class TestNoInventedData:
    def test_no_sequence_contains_a_placeholder(self, uniprot_subset, cycs_family):
        for rec in list(uniprot_subset) + list(cycs_family):
            assert "XXXX" not in rec.sequence
            assert "TODO" not in rec.sequence.upper()

    def test_datasets_readme_declares_real_data(self):
        text = (REPO / "datasets" / "README.md").read_text(encoding="utf-8")
        assert "REAL" in text.upper()
        assert "UniProt" in text
