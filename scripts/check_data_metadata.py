#!/usr/bin/env python3
"""Verify that every dataset on disk is described by metadata that matches it.

Three failure modes this catches, all of which happened during development:

1. a data file was edited and its recorded ``sha256`` was not updated;
2. a metadata file described a dataset that is not in the repository (or vice versa);
3. a dataset was written without provenance — no source, no licence, no
   ``synthetic: true|false`` flag.

For this repository the data are *real* (UniProt, CC BY 4.0), so provenance is a licence
condition, not a nicety: shipping the file without its source and licence would be a
copyright problem as well as a documentation one.

    python scripts/check_data_metadata.py
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
SAMPLE = REPO / "datasets" / "sample"
META = REPO / "datasets" / "metadata"

REQUIRED_KEYS = {
    "dataset", "file", "synthetic", "source", "retrieved", "license",
    "attribution", "description", "sha256", "bytes", "records", "regenerate",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def count_records(path: Path) -> int:
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.startswith(">"))


def main() -> int:
    problems: list[str] = []

    data_stems = {p.stem for p in SAMPLE.glob("*.fasta")}
    meta_stems = {p.stem for p in META.glob("*.yml")}

    for missing in sorted(data_stems - meta_stems):
        problems.append(f"{missing}.fasta: no metadata file in {META.relative_to(REPO)}/")
    for orphan in sorted(meta_stems - data_stems):
        problems.append(f"{orphan}.yml: metadata with no matching data file")

    for meta_path in sorted(META.glob("*.yml")):
        meta = yaml.safe_load(meta_path.read_text(encoding="utf-8")) or {}
        name = meta_path.stem
        missing_keys = REQUIRED_KEYS - set(meta)
        if missing_keys:
            problems.append(f"{name}: metadata missing keys {sorted(missing_keys)}")
            continue
        if not isinstance(meta["synthetic"], bool):
            problems.append(f"{name}: 'synthetic' must be true or false, not {meta['synthetic']!r}")
        if meta["synthetic"] is False and not str(meta.get("license", "")).startswith("CC BY"):
            problems.append(f"{name}: real data must record a reusable licence (found {meta.get('license')!r})")

        target = REPO / meta["file"]
        if not target.is_file():
            problems.append(f"{name}: {meta['file']} does not exist")
            continue
        before = len(problems)
        actual_hash = sha256(target)
        if actual_hash != meta["sha256"]:
            problems.append(
                f"{name}: sha256 mismatch — file {actual_hash[:16]}…, metadata {str(meta['sha256'])[:16]}…"
            )
        actual_bytes = target.stat().st_size
        if actual_bytes != meta["bytes"]:
            problems.append(f"{name}: byte size {actual_bytes} != recorded {meta['bytes']}")
        actual_records = count_records(target)
        if actual_records != meta["records"]:
            problems.append(f"{name}: {actual_records} records != recorded {meta['records']}")

        print(f"{'OK  ' if len(problems) == before else 'FAIL'} {meta['file']}: "
              f"{meta['records']} records, {meta['bytes']:,} bytes, synthetic={meta['synthetic']}")

    if problems:
        print("\nPROBLEMS:")
        for p in problems:
            print(f"  - {p}")
        return 1
    print(f"\nOK: every dataset has metadata; all {len(meta_stems)} recorded hashes, sizes and "
          "record counts match the files on disk.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
