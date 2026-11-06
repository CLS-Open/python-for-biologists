#!/usr/bin/env python3
"""Build ``datasets/sample/qc_problems.fasta`` from real records.

This file exists so that the quality-control code has something to find. Each
defect is *planted on purpose* and recorded in
``datasets/metadata/qc_problems.yml`` — the file is real data with documented
damage, not invented data.

Nothing here is random: the output is a pure function of the two source files,
the generator is deterministic, and CI regenerates it and compares hashes.

    python scripts/make_qc_dataset.py
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
SAMPLE = REPO / "datasets" / "sample"
META = REPO / "datasets" / "metadata"

#: (destination id, source accession) — the record each defect is planted in.
PLANTED = [
    ("pl_duplicate", "P99999"),
    ("pl_internal_stop", "P62897"),
    ("pl_invalid_residue", "P62898"),
    ("pl_lowercase_whitespace", "Q6IQM2"),
    ("pl_truncated", "Q6GQE4"),
    ("pl_ambiguous_rich", "P84029"),
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_records(path: Path) -> dict[str, tuple[str, str]]:
    """Very small FASTA reader: {accession: (header, sequence)}."""
    out: dict[str, tuple[str, str]] = {}
    header = ""
    parts: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        if line.startswith(">"):
            if header:
                out[header.split("|")[1]] = (header, "".join(parts))
            header, parts = line[1:], []
        else:
            parts.append(line)
    if header:
        out[header.split("|")[1]] = (header, "".join(parts))
    return out


def wrap(seq: str, width: int = 60) -> str:
    return "\n".join(seq[i : i + width] for i in range(0, len(seq), width))


def main() -> int:
    cycs = read_records(SAMPLE / "gene_family_cycs.fasta")
    missing = [acc for _, acc in PLANTED if acc not in cycs]
    if missing:
        print(f"error: source records missing {missing}; run fetch_datasets.py first", file=sys.stderr)
        return 2

    blocks: list[str] = []
    log: list[dict[str, object]] = []

    for new_id, acc in PLANTED:
        header, seq = cycs[acc]
        original = seq
        note = ""
        if new_id == "pl_duplicate":
            # The realistic failure: someone ran `cat export_1.fasta >> all.fasta`
            # twice. Two records with the same identifier and the same content.
            note = ("written twice, byte-identical (the `cat file >> file` accident); "
                    "the identifier therefore appears twice in the file")
            for _ in range(2):
                blocks.append(f">{acc}|{new_id} {header.split(' ', 1)[1]}\n{wrap(seq)}\n")
        elif new_id == "pl_internal_stop":
            # A stop codon in the middle: what a frameshift or a badly joined
            # exon looks like in a translated protein record.
            pos = len(seq) // 2
            seq = seq[:pos] + "*" + seq[pos + 1 :]
            note = f"residue {pos + 1} changed from {original[pos]!r} to '*' (internal stop)"
            blocks.append(f">{acc}|{new_id} {header.split(' ', 1)[1]}\n{wrap(seq)}\n")
        elif new_id == "pl_invalid_residue":
            seq = seq[:10] + "1" + seq[11:]
            note = f"residue 11 changed from {original[10]!r} to '1' (not a residue letter at all)"
            blocks.append(f">{acc}|{new_id} {header.split(' ', 1)[1]}\n{wrap(seq)}\n")
        elif new_id == "pl_lowercase_whitespace":
            lower = seq.lower()
            # embedding a tab and a double space is realistic copy-paste damage
            seq_lines = [lower[i : i + 60] for i in range(0, len(lower), 60)]
            seq_lines[0] = seq_lines[0][:20] + "  " + seq_lines[0][20:]
            seq_lines[1] = seq_lines[1][:10] + "\t" + seq_lines[1][10:]
            note = "sequence lower-cased; a double space inserted after residue 20 and a tab after residue 70"
            blocks.append(f">{acc}|{new_id} {header.split(' ', 1)[1]}\n" + "\n".join(seq_lines) + "\n")
        elif new_id == "pl_truncated":
            seq = seq[:60]
            note = f"truncated to the first 60 of {len(original)} residues (a cut-off download)"
            blocks.append(f">{acc}|{new_id} {header.split(' ', 1)[1]}\n{wrap(seq)}\n")
        elif new_id == "pl_ambiguous_rich":
            # Replace every fourth residue with X: an alignment that was mostly gaps.
            chars = list(seq)
            for i in range(3, len(chars), 4):
                chars[i] = "X"
            seq = "".join(chars)
            n_x = seq.count("X")
            note = f"every 4th residue replaced with 'X' ({n_x} of {len(seq)} ambiguous)"
            blocks.append(f">{acc}|{new_id} {header.split(' ', 1)[1]}\n{wrap(seq)}\n")
        log.append({"id": new_id, "source_accession": acc, "alteration": note})

    # A record with a header but no sequence: the empty-export failure.
    blocks.append(">pl_empty_record Header present, no data (an interrupted export)\n")
    log.append({"id": "pl_empty_record", "source_accession": None,
                "alteration": "header with no sequence lines at all"})

    path = SAMPLE / "qc_problems.fasta"
    path.write_text("\n".join(blocks), encoding="utf-8")

    meta = {
        "dataset": "qc_problems",
        "file": "datasets/sample/qc_problems.fasta",
        "synthetic": False,
        "source": "derived from datasets/sample/gene_family_cycs.fasta (UniProt records, CC BY 4.0)",
        "retrieved": "2026-11-06",
        "license": "CC BY 4.0 — original data © the UniProt Consortium; alterations by CLS-Open",
        "attribution": "The UniProt Consortium, UniProtKB/Swiss-Prot, https://www.uniprot.org",
        "description": ("Real cytochrome c records with seven defects planted on purpose, "
                        "so that the quality-control checks have something to find. "
                        "Every alteration is listed below."),
        "used_for": "module 3 (functions and error handling) and practical 2 (QC)",
        "planted_defects": log,
        "sha256": sha256(path),
        "bytes": path.stat().st_size,
        "records": path.read_text(encoding="utf-8").count("\n>") + 1,
        "regenerate": "python scripts/make_qc_dataset.py",
    }
    META.mkdir(parents=True, exist_ok=True)
    (META / "qc_problems.yml").write_text(yaml.safe_dump(meta, sort_keys=False), encoding="utf-8")
    print(f"wrote {path.relative_to(REPO)} ({meta['records']} records, {meta['bytes']} bytes)")
    for entry in log:
        print(f"  - {entry['id']}: {entry['alteration']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
