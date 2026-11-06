#!/usr/bin/env python3
"""Retrieve the real datasets this repository ships, and record their provenance.

Nothing here is invented. Every sequence comes from the UniProt REST API, is
identified by its accession in the FASTA header, and is recorded in
``datasets/metadata/<name>.yml`` with the exact query, retrieval date, record
count and sha256 of the file we committed.

Run with no arguments to *verify* (compare recorded sha256 with the files on
disk — this is what CI does). Run with ``--refetch`` to contact UniProt again
and rewrite the files; that requires network access and will change the
retrieval date, so it is a deliberate act, not something CI does.

    python scripts/fetch_datasets.py            # verify committed files
    python scripts/fetch_datasets.py --refetch  # re-download from UniProt

Licence: UniProt data are CC BY 4.0 (https://www.uniprot.org/help/license).
Attribution is carried in ``datasets/metadata/`` and in ``datasets/README.md``.
"""
from __future__ import annotations

import argparse
import hashlib
import sys
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
SAMPLE = REPO / "datasets" / "sample"
META = REPO / "datasets" / "metadata"
API = "https://rest.uniprot.org/uniprotkb/search"
UNIPROT_LICENCE = "CC BY 4.0 (UniProt Terms of Use; data © the UniProt Consortium)"
ATTRIBUTION = "The UniProt Consortium, UniProt Knowledgebase (UniProtKB/Swiss-Prot), https://www.uniprot.org"


def _get(query: str, fmt: str, size: int, sort: str = "accession asc") -> str:
    url = f"{API}?{urllib.parse.urlencode({'query': query, 'format': fmt, 'size': size, 'sort': sort})}"
    req = urllib.request.Request(url, headers={"User-Agent": "cls-open-python-for-biologists/0.1"})
    with urllib.request.urlopen(req, timeout=60) as fh:
        return fh.read().decode("utf-8")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


#: The subset is *stratified by length*, not simply the first 60 hits.
#:
#: The first version of this script asked for ``length:[100 TO 800]`` sorted by
#: accession and took 60 records. That returned an excellent illustration of a
#: sampling artefact: nearly all of them were 100–150 aa, because accession order
#: clusters families (immunoglobulin and keratin fragments) together. The data
#: were real, the "60 diverse human proteins" description was not. Ten proteins
#: per 100-aa length band fixes it, and the story is told in module 4.
LENGTH_BANDS = [(100, 199), (200, 299), (300, 399), (400, 499), (500, 599), (600, 699)]
PER_BAND = 10


def fetch_uniprot_subset() -> tuple[Path, str]:
    """60 reviewed human proteins: 10 per 100-aa length band, accession order.

    Sorted by accession within each band so the file is a function of the query
    alone, not of server-side relevance ranking.
    """
    blocks: list[str] = []
    for low, high in LENGTH_BANDS:
        query = f"organism_id:9606 AND reviewed:true AND length:[{low} TO {high}]"
        text = _get(query, "fasta", PER_BAND)
        blocks.append(text if text.endswith("\n") else text + "\n")
    path = SAMPLE / "uniprot_human_subset.fasta"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(blocks), encoding="utf-8")

    # Guard: exactly the requested number of records, one per accession.
    records = [line for line in path.read_text(encoding="utf-8").splitlines() if line.startswith(">")]
    if len(records) != PER_BAND * len(LENGTH_BANDS):
        raise SystemExit(f"expected {PER_BAND * len(LENGTH_BANDS)} records, got {len(records)}")
    accessions = [h.split("|")[1] for h in records]
    if len(set(accessions)) != len(accessions):
        raise SystemExit("duplicate accessions in the fetched subset")

    query = ("; ".join(
        f"organism_id:9606 AND reviewed:true AND length:[{lo} TO {hi}] -> first {PER_BAND} by accession"
        for lo, hi in LENGTH_BANDS
    ))
    return path, query


#: One canonical cytochrome c per species, identified by UniProt accession.
#: Chosen by searching the UniProt web interface on 2026-11-06 for
#: ``protein_name:"Cytochrome c" AND reviewed:true`` restricted to the species
#: and to 90–120 aa, then taking the entry whose annotation names it plain
#: "Cytochrome c" (not a c1/b5/oxidase/biogenesis factor).
#:
#: Orthology caveat, stated because the capstone depends on it: gene naming is
#: not conserved. Fly has Cyt-c-p/Cyt-c-d; yeast has CYC1 plus a second isoform;
#: Arabidopsis has CYTC-1/2. These eight entries are the best-annotated
#: single-copy cytochrome c in each species according to UniProt annotation —
#: that is a curation claim, not a phylogenetic one. The capstone asks learners
#: to interrogate exactly this assumption.
CYCS_ORTHOLOGUES = [
    ("P99999", "Homo sapiens", "CYCS"),
    ("P62897", "Mus musculus", "Cycs"),
    ("P62898", "Rattus norvegicus", "Cycs"),
    ("Q6IQM2", "Danio rerio", "cyc"),
    ("Q6GQE4", "Xenopus laevis", "cycs-a"),
    ("P84029", "Drosophila melanogaster", "Cyt-c-p"),
    ("P00044", "Saccharomyces cerevisiae", "CYC1"),
    ("P29380", "Arabidopsis thaliana", "CC-1"),
]


def fetch_gene_family() -> tuple[Path, str]:
    """Fetch the eight curated cytochrome c entries by accession.

    Fetching by accession rather than by re-running a search makes the file a
    pure function of a documented accession list: a search would silently
    change if UniProt's ranking or curation changed.
    """
    accessions = ",".join(a for a, _, _ in CYCS_ORTHOLOGUES)
    url = ("https://rest.uniprot.org/uniprotkb/accessions?"
           + urllib.parse.urlencode({"accessions": accessions, "format": "fasta"}))
    req = urllib.request.Request(url, headers={"User-Agent": "cls-open-python-for-biologists/0.1"})
    with urllib.request.urlopen(req, timeout=60) as fh:
        text = fh.read().decode("utf-8")
    path = SAMPLE / "gene_family_cycs.fasta"
    path.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")

    # Guard: the file must contain exactly the eight requested accessions, in
    # order, and nothing else. A silent substitution here would poison the
    # capstone.
    got = [line[1:].split("|")[1] for line in text.splitlines() if line.startswith(">")]
    expected = [a for a, _, _ in CYCS_ORTHOLOGUES]
    if got != expected:
        raise SystemExit(f"accession mismatch: expected {expected}, got {got}")
    query = ("accessions=" + accessions + " (curated cytochrome c orthologues: "
             + "; ".join(f"{a} {sp} {gene}" for a, sp, gene in CYCS_ORTHOLOGUES) + ")")
    return path, query


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--refetch", action="store_true", help="contact UniProt and rewrite the data files")
    args = ap.parse_args()

    if not args.refetch:
        return verify()

    META.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    jobs = [
        ("uniprot_human_subset", fetch_uniprot_subset,
         "60 reviewed human (taxid 9606) UniProtKB/Swiss-Prot entries, 10 per 100-aa band from 100 to 699 aa",
         "sequence statistics, composition, molecular weight, windowed plots"),
        ("gene_family_cycs", fetch_gene_family,
         "cytochrome c (CYCS) orthologues, one reviewed entry per species, 8 species",
         "the capstone: characterise one gene family across species"),
    ]
    for name, fn, description, used_for in jobs:
        path, query = fn()
        meta = {
            "dataset": name,
            "file": f"datasets/sample/{path.name}",
            "synthetic": False,
            "source": "UniProt REST API — " + API,
            "query": query,
            "retrieved": today,
            "license": UNIPROT_LICENCE,
            "attribution": ATTRIBUTION,
            "description": description,
            "used_for": used_for,
            "sha256": _sha256(path),
            "bytes": path.stat().st_size,
            "records": path.read_text(encoding="utf-8").count("\n>") + 1,
            "regenerate": "python scripts/fetch_datasets.py --refetch",
        }
        (META / f"{name}.yml").write_text(yaml.safe_dump(meta, sort_keys=False), encoding="utf-8")
        print(f"wrote {path.relative_to(REPO)} ({meta['records']} records, {meta['bytes']} bytes)")
    print("\nNow make the derived QC dataset: python scripts/make_qc_dataset.py")
    return 0


def verify() -> int:
    """Compare recorded sha256 with the files on disk. No network."""
    failures = 0
    for meta_path in sorted(META.glob("*.yml")):
        meta = yaml.safe_load(meta_path.read_text(encoding="utf-8"))
        target = REPO / meta["file"]
        if not target.is_file():
            print(f"FAIL {meta_path.name}: missing {meta['file']}")
            failures += 1
            continue
        got = _sha256(target)
        ok = got == meta["sha256"]
        failures += not ok
        print(f"{'OK  ' if ok else 'FAIL'} {meta['file']}: sha256 {got[:16]}… "
              f"({'matches' if ok else 'DOES NOT MATCH'} metadata)")
    if failures:
        print(f"\n{failures} dataset(s) do not match their metadata")
        return 1
    print("\nAll committed datasets match their recorded sha256.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
