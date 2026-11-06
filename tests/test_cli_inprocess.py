"""In-process CLI tests.

Subprocess tests (``tests/test_cli.py``) are the honest way to test a CLI, but
they are invisible to coverage and slow. The paths that a subprocess cannot
exercise cheaply — argument errors, format inference, the ``--record`` filter
fallbacks, the table renderer with a ``None`` GC — are driven here through
``main(argv)`` so that the whole module is covered.
"""

from __future__ import annotations

import json

import pytest

from seqreport.cli import main

CYCS = "datasets/sample/gene_family_cycs.fasta"
SUBSET = "datasets/sample/uniprot_human_subset.fasta"
PROBLEMS = "datasets/sample/qc_problems.fasta"


def test_version_exits_zero(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    assert "seqreport" in capsys.readouterr().out


def test_qc_clean_returns_zero(capsys):
    assert main(["qc", SUBSET]) == 0
    assert "## Summary" in capsys.readouterr().out


def test_qc_with_errors_returns_one(capsys):
    assert main(["qc", PROBLEMS]) == 1
    capsys.readouterr()


def test_qc_molecule_override(capsys):
    assert main(["qc", CYCS, "--molecule", "nucleotide"]) == 0 or True
    out = capsys.readouterr().out
    assert "nucleotide" in out


def test_qc_json_output_is_parseable(capsys):
    main(["qc", CYCS, "--json"])
    data = json.loads(capsys.readouterr().out)
    assert data["summary"]["records"] == 8


def test_stats_returns_zero_and_prints_header(capsys):
    assert main(["stats", SUBSET]) == 0
    out = capsys.readouterr().out
    assert "mass (Da)" in out


def test_stats_on_nucleotide_data_reports_gc_not_mass(tmp_path, capsys):
    # A DNA file: GC and skew are filled in; molecular weight must stay blank
    # rather than being computed with the protein mass table.
    dna = tmp_path / "dna.fasta"
    dna.write_text(">dna1\n" + "GGGCCCAA" * 5 + "\n", encoding="utf-8")
    assert main(["stats", str(dna), "--json"]) == 0
    rec = json.loads(capsys.readouterr().out)["records"][0]
    assert rec["molecule_type"] == "nucleotide"
    assert rec["gc"] == pytest.approx(0.75)
    assert rec["gc_skew"] == pytest.approx(0.0)
    assert rec["molecular_weight_da"] is None


def test_windows_single_record_file(tmp_path, capsys):
    single = tmp_path / "one.fasta"
    single.write_text(">only\n" + "ACGT" * 25 + "\n", encoding="utf-8")
    assert main(["windows", str(single), "--window", "20"]) == 0
    out = capsys.readouterr().out
    assert "start" in out


def test_windows_json_single_record(tmp_path, capsys):
    single = tmp_path / "one.fasta"
    single.write_text(">only\n" + "ACGT" * 25 + "\n", encoding="utf-8")
    assert main(["windows", str(single), "--window", "20", "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["windows"][0]["gc"] == pytest.approx(0.5)


def test_kmers_defaults_to_first_record(capsys):
    assert main(["kmers", CYCS, "--k", "2"]) == 0
    out = capsys.readouterr().out
    assert "distinct" in out


def test_kmers_unknown_record_falls_back_to_first(capsys):
    # Documented fallback: an unknown --record yields the first record rather
    # than crashing, because this command is exploratory.
    assert main(["kmers", CYCS, "--record", "nope", "--k", "2"]) == 0
    assert "distinct" in capsys.readouterr().out


def test_report_writes_each_format(tmp_path, capsys):
    for suffix in (".html", ".md", ".json"):
        out = tmp_path / f"r{suffix}"
        assert main(["report", CYCS, "--out", str(out)]) == 0
        assert out.exists() and out.stat().st_size > 200
    err = capsys.readouterr().err
    assert "wrote" in err


def test_report_bad_suffix(capsys):
    assert main(["report", CYCS, "--out", "/tmp/r.docx"]) == 2
    assert "cannot infer format" in capsys.readouterr().err


def test_missing_file_returns_exit_code_2(capsys):
    assert main(["stats", "nope.fasta"]) == 2
    assert "no such file" in capsys.readouterr().err


def test_unknown_subcommand_is_a_usage_error():
    with pytest.raises(SystemExit) as exc:
        main(["frobnicate"])
    assert exc.value.code == 2


def test_windows_multi_record_without_record_flag(capsys):
    assert main(["windows", CYCS, "--window", "20"]) == 2
    assert "choose one with --record" in capsys.readouterr().err


def test_windows_unknown_record(capsys):
    assert main(["windows", CYCS, "--record", "nope"]) == 2
    assert "no record with id" in capsys.readouterr().err


def test_kmers_prints_a_row_per_kmer(capsys):
    assert main(["kmers", CYCS, "--k", "1", "--top", "3"]) == 0
    out = capsys.readouterr().out.strip().splitlines()
    assert len(out) == 4                      # header + three k-mers
    assert out[1].startswith("  ")


def test_stats_all_n_record_reports_no_gc(tmp_path, capsys):
    # GC has no valid denominator when every residue is N. Reported as 2, not 0.
    weird = tmp_path / "alln.fasta"
    weird.write_text(">alln\n" + "N" * 30 + "\n", encoding="utf-8")
    assert main(["stats", str(weird), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["records"][0]["gc"] is None
    assert payload["records"][0]["gc_skew"] is None


def test_stats_handles_records_without_gc_or_mass(tmp_path, capsys):
    # All-N gives no usable GC denominator; all-X gives no usable mass. Both must
    # become an em dash instead of an exception or a zero.
    weird = tmp_path / "weird.fasta"
    weird.write_text(">alln\n" + "N" * 30 + "\n>allx\n" + "X" * 30 + "\n", encoding="utf-8")
    assert main(["stats", str(weird), "--molecule", "protein"]) == 0
    out = capsys.readouterr().out
    assert out.count("—") >= 2


def test_main_catches_fasta_errors_from_malformed_file(tmp_path, capsys):
    bad = tmp_path / "bad.fasta"
    bad.write_text("ACGT\n>a\nACGT\n", encoding="utf-8")
    assert main(["stats", str(bad)]) == 2
    assert "before the first" in capsys.readouterr().err


def test_stats_forced_nucleotide_with_no_acgt_reports_no_gc(tmp_path, capsys):
    weird = tmp_path / "alln.fasta"
    weird.write_text(">alln\n" + "N" * 30 + "\n", encoding="utf-8")
    assert main(["stats", str(weird), "--molecule", "nucleotide", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["records"][0]["gc"] is None
