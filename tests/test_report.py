"""Tests for the three report renderings.

The property that matters: **the renderings cannot disagree**, because they are
generated from one data structure. The tests check that property directly rather
than checking each renderer's prose.
"""

from __future__ import annotations

import json
import re

import pytest

from seqreport.qc import CheckOptions
from seqreport.records import Record
from seqreport.report import build_report, to_html, to_json, to_markdown

PROTEIN = "MEEPQSDPSVEPPLSQETFSDLWKLLPENNVLSPLPSQAMDDLMLSPDDIEQWFTEDPGP"
DNA = "ACGT" * 10


def report_of(*records, **kwargs):
    return build_report(list(records), source="test.fasta", **kwargs)


class TestBuildReport:
    def test_one_row_per_record(self):
        r = report_of(Record("a", "d", PROTEIN), Record("b", "d", DNA))
        assert [row.id for row in r.records] == ["a", "b"]

    def test_gc_only_for_nucleotides(self):
        r = report_of(Record("p", "d", PROTEIN), Record("n", "d", DNA))
        by_id = {row.id: row for row in r.records}
        assert by_id["p"].gc is None
        assert by_id["n"].gc == pytest.approx(0.5)

    def test_mass_only_for_proteins(self):
        r = report_of(Record("p", "d", PROTEIN), Record("n", "d", DNA))
        by_id = {row.id: row for row in r.records}
        assert by_id["p"].molecular_weight is not None
        assert by_id["n"].molecular_weight is None

    def test_declared_molecule_type_overrides_the_guess(self):
        r = report_of(Record("n", "d", DNA), options=CheckOptions(molecule_type="protein"))
        assert r.records[0].molecule_type == "protein"
        assert r.records[0].molecular_weight is not None

    def test_top_residues_are_ordered_by_count(self):
        r = report_of(Record("p", "d", "AAAA" + PROTEIN))
        counts = [c for _, c in r.records[0].top_residues]
        assert counts == sorted(counts, reverse=True)

    def test_file_level_issue_is_not_duplicated_per_record(self):
        rec = Record("dup", "d", PROTEIN)
        r = report_of(rec, rec)
        assert [i.code for i in r.file_issues] == ["duplicate_id"]
        assert all(not row.issues for row in r.records)

    def test_summary_is_present(self):
        r = report_of(Record("p", "d", PROTEIN))
        assert r.summary.records == 1
        assert r.summary.residues == len(PROTEIN)

    def test_notes_are_carried_through(self):
        r = report_of(Record("p", "d", PROTEIN), notes=["synthetic check"])
        assert "synthetic check" in r.notes

    def test_options_are_recorded_so_the_report_is_self_describing(self):
        r = report_of(Record("p", "d", PROTEIN), options=CheckOptions(min_length=99))
        assert r.as_dict()["options"]["min_length"] == 99


class TestJson:
    def test_is_valid_json(self):
        r = report_of(Record("p", "d", PROTEIN))
        assert json.loads(to_json(r))["records"][0]["id"] == "p"

    def test_round_trips_all_fields(self):
        r = report_of(Record("p", "d", PROTEIN), Record("n", "d", DNA))
        data = json.loads(to_json(r))
        assert set(data) == {"source", "generated_by", "options", "notes", "summary",
                             "file_issues", "records"}

    def test_none_is_kept_not_omitted(self):
        # A missing key and a null mean different things to a consumer.
        r = report_of(Record("n", "d", DNA))
        assert json.loads(to_json(r))["records"][0]["molecular_weight_da"] is None

    def test_numbers_are_rounded_but_not_mangled(self):
        r = report_of(Record("p", "d", PROTEIN))
        value = json.loads(to_json(r))["records"][0]["molecular_weight_da"]
        assert isinstance(value, float)
        assert 0 < value < 100_000


class TestMarkdown:
    def test_has_the_expected_sections(self):
        md = to_markdown(report_of(Record("p", "d", PROTEIN)))
        for heading in ("# seqreport", "## Summary", "## Records", "## Issues"):
            assert heading in md

    def test_every_record_appears(self):
        md = to_markdown(report_of(Record("alpha", "d", PROTEIN), Record("beta", "d", PROTEIN)))
        assert "`alpha`" in md and "`beta`" in md

    def test_clean_file_says_so_without_overclaiming(self):
        md = to_markdown(report_of(Record("p", "d", PROTEIN)))
        assert "No issues found" in md
        assert "not about the data" in md

    def test_issue_rows_are_present(self):
        md = to_markdown(report_of(Record("short", "d", "MEEP")))
        assert "`short_sequence`" in md

    def test_file_issues_get_their_own_section(self):
        rec = Record("dup", "d", PROTEIN)
        md = to_markdown(report_of(rec, rec))
        assert "### File-level" in md

    def test_gc_rendered_as_percentage(self):
        md = to_markdown(report_of(Record("n", "d", DNA)))
        assert "50.0%" in md


class TestHtml:
    def test_is_html(self):
        html = to_html(report_of(Record("p", "d", PROTEIN)))
        assert html.lstrip().startswith("<!DOCTYPE html>")

    def test_has_no_external_resources(self):
        html = to_html(report_of(Record("p", "d", PROTEIN)))
        assert not re.search(r'(src|href)\s*=\s*"https?://', html)
        assert "<script" not in html.lower()

    def test_styles_are_inline(self):
        html = to_html(report_of(Record("p", "d", PROTEIN)))
        assert "<style>" in html

    def test_declares_utf8_and_viewport(self):
        html = to_html(report_of(Record("p", "d", PROTEIN)))
        assert 'charset="utf-8"' in html
        assert 'name="viewport"' in html

    def test_record_ids_are_escaped(self):
        # A header is untrusted input; an id containing markup must not become markup.
        html = to_html(report_of(Record("<script>alert(1)</script>", "d", PROTEIN)))
        assert "<script>alert(1)</script>" not in html
        assert "&lt;script&gt;" in html

    def test_html_and_markdown_agree_on_counts(self):
        recs = [Record("a", "d", PROTEIN), Record("b", "d", "MEEP")]
        rp = report_of(*recs)
        html = to_html(rp)
        md = to_markdown(rp)
        assert f"{rp.summary.records}" in html
        assert f"| {rp.summary.records} |" in md

    def test_size_is_small_enough_to_email(self):
        html = to_html(report_of(Record("p", "d", PROTEIN)))
        assert len(html) < 20_000


class TestDegenerateRecords:
    def test_all_n_record_has_no_gc(self):
        r = report_of(Record("n", "d", "N" * 30))
        assert r.records[0].gc is None

    def test_all_x_record_has_no_mass(self):
        r = report_of(Record("x", "d", "X" * 30), options=CheckOptions(molecule_type="protein"))
        assert r.records[0].molecular_weight is None

    def test_empty_record_has_no_stats(self):
        r = report_of(Record("e", "d", ""))
        assert r.records[0].gc is None
        assert r.records[0].molecular_weight is None


class TestNotesAndDegenerateNucleotide:
    def test_forced_nucleotide_all_n_has_no_gc(self):
        r = report_of(Record("n", "d", "N" * 30), options=CheckOptions(molecule_type="nucleotide"))
        assert r.records[0].gc is None

    def test_notes_appear_in_markdown(self):
        r = report_of(Record("p", "d", PROTEIN), notes=["data retrieved 2026-11-06"])
        assert "data retrieved 2026-11-06" in to_markdown(r)

    def test_notes_appear_in_html(self):
        r = report_of(Record("p", "d", PROTEIN), notes=["data retrieved 2026-11-06"])
        assert "data retrieved 2026-11-06" in to_html(r)
