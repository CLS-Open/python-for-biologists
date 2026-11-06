"""CLI tests, run through a subprocess exactly as a learner runs it.

Exit codes are part of the interface: CI gates on them, so they are tested like
any other output.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SAMPLE = REPO / "datasets" / "sample"
CYCS = SAMPLE / "gene_family_cycs.fasta"
SUBSET = SAMPLE / "uniprot_human_subset.fasta"
PROBLEMS = SAMPLE / "qc_problems.fasta"


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-m", "seqreport.cli", *args],
                          capture_output=True, text=True)


def test_version():
    r = run("--version")
    assert r.returncode == 0
    assert "seqreport 0.1.0" in r.stdout


def test_help_lists_every_subcommand():
    r = run("--help")
    assert r.returncode == 0
    for cmd in ("qc", "stats", "windows", "kmers", "report"):
        assert cmd in r.stdout


def test_requiring_a_command():
    r = run()
    assert r.returncode != 0


def test_missing_file_exits_2():
    r = run("stats", "does_not_exist.fasta")
    assert r.returncode == 2
    assert "no such file" in r.stderr


def test_stats_table_on_gene_family():
    r = run("stats", str(CYCS))
    assert r.returncode == 0
    assert "8 record(s); molecule type: protein" in r.stdout
    assert "11,748.6" in r.stdout          # P99999 mass, cross-checked elsewhere


def test_stats_json_is_pipeable():
    r = run("stats", str(CYCS), "--json")
    assert r.returncode == 0
    data = json.loads(r.stdout)         # stderr may contain chatter; stdout must not
    assert data["molecule_type"] == "protein"
    assert len(data["records"]) == 8
    assert data["records"][0]["molecular_weight_da"] == pytest.approx(11748.6, abs=0.1)


def test_qc_clean_file_exits_0():
    r = run("qc", str(SUBSET))
    assert r.returncode == 0
    assert "| 60 |" in r.stdout


def test_qc_planted_file_exits_1_and_reports_errors():
    r = run("qc", str(PROBLEMS))
    assert r.returncode == 1
    assert "duplicate_id" in r.stdout
    assert "empty_sequence" in r.stdout


def test_qc_json_has_file_issues():
    r = run("qc", str(PROBLEMS), "--json")
    data = json.loads(r.stdout)
    assert data["summary"]["errors"] >= 2
    assert any(i["code"] == "duplicate_id" for i in data["file_issues"])


def test_qc_min_length_option_changes_the_verdict():
    r = run("qc", str(CYCS), "--min-length", "107")
    assert r.returncode == 0        # warnings only, no errors
    assert "short_sequence" in r.stdout


def test_windows_needs_a_record_when_multiple_present():
    r = run("windows", str(CYCS))
    assert r.returncode == 2
    assert "choose one with --record" in r.stderr


def test_windows_with_record():
    r = run("windows", str(CYCS), "--record", "sp|P99999|CYC_HUMAN", "--window", "21")
    assert r.returncode == 0
    assert "start" in r.stdout


def test_windows_json():
    r = run("windows", str(CYCS), "--record", "sp|P99999|CYC_HUMAN", "--window", "35", "--json")
    data = json.loads(r.stdout)
    assert data["record"] == "sp|P99999|CYC_HUMAN"
    assert data["window"] == 35
    assert len(data["windows"]) == 3


def test_windows_unknown_record_exits_2():
    r = run("windows", str(CYCS), "--record", "not_a_record")
    assert r.returncode == 2
    assert "no record with id" in r.stderr


def test_kmers_table():
    r = run("kmers", str(CYCS), "--record", "sp|P99999|CYC_HUMAN", "--k", "2", "--top", "3")
    assert r.returncode == 0
    assert "k=2" in r.stdout


def test_kmers_json_totals_match_sequence_length():
    r = run("kmers", str(CYCS), "--record", "sp|P99999|CYC_HUMAN", "--k", "3", "--json")
    data = json.loads(r.stdout)
    assert data["total"] == 105 - 3 + 1


def test_report_html_written(tmp_path):
    out = tmp_path / "r.html"
    r = run("report", str(CYCS), "--out", str(out))
    assert r.returncode == 0
    assert out.read_text().startswith("<!DOCTYPE html>")
    assert "wrote" in r.stderr


def test_report_markdown_written(tmp_path):
    out = tmp_path / "r.md"
    r = run("report", str(PROBLEMS), "--out", str(out))
    assert r.returncode == 0
    assert "## Issues" in out.read_text()


def test_report_json_written(tmp_path):
    out = tmp_path / "r.json"
    run("report", str(CYCS), "--out", str(out))
    assert json.loads(out.read_text())["summary"]["records"] == 8


def test_report_rejects_unknown_extension(tmp_path):
    r = run("report", str(CYCS), "--out", str(tmp_path / "r.pdf"))
    assert r.returncode == 2
    assert "cannot infer format" in r.stderr


def test_gzipped_input_works(tmp_path):
    import gzip

    gz = tmp_path / "cycs.fasta.gz"
    with gzip.open(gz, "wt", encoding="utf-8") as fh:
        fh.write(CYCS.read_text())
    r = run("stats", str(gz), "--json")
    assert r.returncode == 0
    assert len(json.loads(r.stdout)["records"]) == 8
