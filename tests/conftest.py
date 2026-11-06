"""Shared fixtures.

Fixtures load the *committed* datasets rather than building toy data in the test,
so the tests exercise the files learners actually get. If the data changes, the
tests that depend on its properties fail loudly.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from seqreport.records import read_fasta  # noqa: E402

SAMPLE = REPO / "datasets" / "sample"


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO


@pytest.fixture(scope="session")
def uniprot_subset():
    return read_fasta(SAMPLE / "uniprot_human_subset.fasta")


@pytest.fixture(scope="session")
def cycs_family():
    return read_fasta(SAMPLE / "gene_family_cycs.fasta")


@pytest.fixture(scope="session")
def planted_records():
    return read_fasta(SAMPLE / "qc_problems.fasta")
