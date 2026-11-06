"""seqreport — biological record quality control and composition reporting.

`seqreport` is deliberately small and dependency-free: it exists so that a
learner can read every line of it. It does four things and nothing else:

1. parse FASTA records (streaming, gzip-aware, strict about malformed input);
2. compute composition statistics (counts, GC, skew, molecular weight, windows);
3. check record quality and report issues by severity;
4. render the result as text, JSON, Markdown or a self-contained HTML page.

The algorithms are *not* the subject here — `bioinformatics-foundations`
(repository #4) is where alignment and translation live. Here Python is the
subject: packages, tests, error handling, CLI design and reproducible reports.

Example
-------
>>> from seqreport import parse_fasta, gc_content, check_records
>>> list(parse_fasta("datasets/sample/gene_family_cycs.fasta"))[0].id  # doctest: +SKIP
'P99999'
"""

from __future__ import annotations

__version__ = "0.1.0"
__all__ = [
    "__version__",
    "Record",
    "FastaError",
    "parse_fasta",
    "read_fasta",
    "write_fasta",
    "guess_molecule_type",
    "composition",
    "gc_content",
    "gc_skew",
    "at_skew",
    "molecular_weight",
    "kmer_counts",
    "windowed_gc",
    "Issue",
    "check_records",
    "summarise",
    "RecordReport",
    "build_report",
    "to_json",
    "to_markdown",
    "to_html",
]

from .composition import (
    at_skew,
    composition,
    gc_content,
    gc_skew,
    kmer_counts,
    molecular_weight,
    windowed_gc,
)
from .qc import Issue, check_records, summarise
from .records import FastaError, Record, guess_molecule_type, parse_fasta, read_fasta, write_fasta
from .report import RecordReport, build_report, to_html, to_json, to_markdown
