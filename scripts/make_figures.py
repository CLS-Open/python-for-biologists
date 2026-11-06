#!/usr/bin/env python3
"""Regenerate every figure from the committed datasets.

Determinism rules (learned the hard way, and enforced by CI):

* never iterate over a ``set`` or a ``dict`` whose order depends on hashing —
  sort first, or the PNG bytes change between runs;
* no random numbers without a seed;
* no timestamps, no hostnames, no absolute paths in the output;
* fixed DPI, fixed figure size, ``metadata={"Software": None}`` on save so the
  Matplotlib version string does not leak into the file.

    python scripts/make_figures.py          # writes figures/*.png
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")           # no display needed, and no GUI in CI

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np               # noqa: E402

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from seqreport.composition import composition, kmer_counts  # noqa: E402
from seqreport.qc import check_records  # noqa: E402
from seqreport.records import read_fasta  # noqa: E402

FIGURES = REPO / "figures"
SAMPLE = REPO / "datasets" / "sample"

#: House style: readable at 50% width in a browser, colour-blind safe pairs.
BLUE = "#2a6f97"
ORANGE = "#d97706"
RED = "#9b2226"
GREY = "#6b7280"
AA_ORDER = "ACDEFGHIKLMNPQRSTVWY"


def species_name(record) -> str:
    """Short binomial from a UniProt description ('Homo sapiens (Human)' -> 'Homo sapiens')."""
    full = record.description.split("OS=")[1].split(" OX=")[0]
    return " ".join(full.split(" (")[0].split()[:2])

plt.rcParams.update({
    "figure.dpi": 150,
    "savefig.dpi": 150,
    "font.size": 9,
    "axes.titlesize": 10,
    "axes.labelsize": 9,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.25,
    "grid.linewidth": 0.6,
    "figure.autolayout": False,
})


def save(fig, name: str) -> Path:
    FIGURES.mkdir(exist_ok=True)
    path = FIGURES / name
    fig.savefig(path, dpi=150, bbox_inches="tight", metadata={"Software": None})
    plt.close(fig)
    print(f"wrote {path.relative_to(REPO)} ({path.stat().st_size:,} bytes)")
    return path


def fig01_length_distribution() -> Path:
    """Figure 1 — how long are the 60 real proteins we ship?"""
    records = read_fasta(SAMPLE / "uniprot_human_subset.fasta")
    lengths = np.array(sorted(len(r) for r in records))
    fig, ax = plt.subplots(figsize=(6.0, 3.4))
    bins = np.arange(0, lengths.max() + 50, 50)
    ax.hist(lengths, bins=bins, color=BLUE, edgecolor="white", linewidth=0.8)
    median = float(np.median(lengths))
    ax.axvline(median, color=ORANGE, linewidth=1.4, linestyle="--",
               label=f"median = {median:.0f} aa")
    ax.set_xlabel("protein length (amino acids)")
    ax.set_ylabel("number of proteins")
    ax.set_ylim(0, 11.5)     # headroom so the annotation does not sit on a bar
    ax.set_title("Figure 1 — Lengths of the 60 reviewed human proteins in the dataset")
    ax.legend(frameon=False, loc="upper right", bbox_to_anchor=(1.0, 1.0))
    # The flat shape is a property of the *sampling design* (10 proteins per
    # 100-aa band), not of the human proteome. The figure says so.
    ax.text(0.015, 0.95,
            f"n = {len(lengths)} · range {lengths.min()}–{lengths.max()} aa\n"
            "sampled 10 per 100-aa band, so the flat shape is the design",
            transform=ax.transAxes, ha="left", va="top", color=GREY, fontsize=7.5,
            bbox=dict(boxstyle="round,pad=0.25", facecolor="white", edgecolor="none", alpha=0.85))
    return save(fig, "fig01_length_distribution.png")


def fig02_composition_heatmap() -> Path:
    """Figure 2 — amino-acid composition of the eight cytochrome c orthologues."""
    records = read_fasta(SAMPLE / "gene_family_cycs.fasta")
    species = [species_name(r) for r in records]
    matrix = np.zeros((len(records), len(AA_ORDER)))
    for i, rec in enumerate(records):
        counts = composition(rec.sequence)
        total = sum(counts.values())
        for j, aa in enumerate(AA_ORDER):
            matrix[i, j] = 100.0 * counts.get(aa, 0) / total
    fig, ax = plt.subplots(figsize=(7.4, 3.2))
    im = ax.imshow(matrix, aspect="auto", cmap="viridis")
    ax.set_xticks(range(len(AA_ORDER)), labels=list(AA_ORDER))
    ax.set_yticks(range(len(species)), labels=species)
    ax.set_xlabel("amino acid")
    ax.set_title("Figure 2 — Amino-acid composition of cytochrome c orthologues (% of residues)")
    ax.grid(False)
    cbar = fig.colorbar(im, ax=ax, pad=0.02)
    cbar.set_label("% of residues in the sequence")
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            if matrix[i, j] >= 8:
                # White only where the colormap is dark enough for it to read.
                ax.text(j, i, f"{matrix[i, j]:.0f}", ha="center", va="center",
                        color="white" if matrix[i, j] >= 14 else "#1f2937", fontsize=6.0)
    return save(fig, "fig02_composition_heatmap.png")


def kmer_jaccard(a: str, b: str, k: int) -> float:
    """Jaccard similarity between the sets of k-mers of two sequences."""
    ka, kb = set(kmer_counts(a, k)), set(kmer_counts(b, k))
    if not ka and not kb:
        return 1.0
    return len(ka & kb) / len(ka | kb)


def fig03_kmer_similarity() -> Path:
    """Figure 3 — k-mer similarity to human cytochrome c, and why it is not identity."""
    records = read_fasta(SAMPLE / "gene_family_cycs.fasta")
    human = next(r for r in records if r.accession == "P99999")
    species = [species_name(r) for r in records if r.accession != "P99999"]
    others = [r for r in records if r.accession != "P99999"]
    ks = list(range(1, 8))
    fig, ax = plt.subplots(figsize=(6.2, 3.6))
    colours = [BLUE, ORANGE, RED, GREY, "#5f0f40", "#0f766e", "#7c2d12"]
    for colour, name, rec in zip(colours, species, others):
        ys = [kmer_jaccard(human.sequence, rec.sequence, k) for k in ks]
        ax.plot(ks, ys, marker="o", markersize=3.5, linewidth=1.4, color=colour, label=name)
    ax.set_xlabel("k-mer length k")
    ax.set_ylabel("Jaccard similarity of k-mer sets")
    ax.set_ylim(0, 1.22)
    ax.set_yticks([0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_xticks(ks)
    ax.set_title("Figure 3 — k-mer similarity to human cytochrome c (P99999)")
    ax.legend(frameon=False, fontsize=7, ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.17),
              handlelength=1.4, columnspacing=1.2)
    ax.text(0.5, 0.98,
            "Similarity falls as k grows because the sequences differ.\n"
            "k-mer similarity is NOT percent identity.",
            transform=ax.transAxes, ha="center", va="top", fontsize=7, color=GREY,
            bbox=dict(boxstyle="round,pad=0.25", facecolor="white", edgecolor="none", alpha=0.85))
    return save(fig, "fig03_kmer_similarity.png")


def fig04_qc_dashboard() -> Path:
    """Figure 4 — the checker is loud on damaged data and quiet on clean data.

    A chart of issue counts in the damaged file is all ones, which says nothing.
    The useful question is the one a reviewer asks: does the checker *also* fire on
    good data? So both files are shown, as the worst severity reached per record.
    """
    clean_records = read_fasta(SAMPLE / "uniprot_human_subset.fasta")
    damaged_records = read_fasta(SAMPLE / "qc_problems.fasta")

    def status_counts(records) -> dict[str, int]:
        # File-level issues (duplicate ids) still name the record they concern,
        # so they are included here: a duplicate record is not a clean record.
        worst: dict[str, str] = {}
        rank = {"error": 3, "warning": 2, "info": 1}
        for issue in check_records(records):
            current = worst.get(issue.record_id)
            if current is None or rank[issue.severity] > rank[current]:
                worst[issue.record_id] = issue.severity
        counts = {"clean": 0, "error": 0, "warning": 0, "info": 0}
        for rec in records:
            counts[worst.get(rec.id, "clean")] += 1
        return counts

    clean = status_counts(clean_records)
    damaged = status_counts(damaged_records)
    categories = ["clean", "info", "warning", "error"]
    colours = {"clean": "#4d7c0f", "info": BLUE, "warning": ORANGE, "error": RED}

    fig, ax = plt.subplots(figsize=(6.6, 2.8))
    labels = [
        f"uniprot_human_subset\n({len(clean_records)} real records, undamaged)",
        f"qc_problems\n({len(damaged_records)} records, 7 defects planted)",
    ]
    left = np.zeros(2)
    for cat in categories:
        values = np.array([clean[cat], damaged[cat]], dtype=float)
        ax.barh([0, 1], values, left=left, color=colours[cat], label=cat,
                edgecolor="white", linewidth=0.8)
        for y, (value, offset) in enumerate(zip(values, left)):
            if value:
                ax.text(offset + value / 2, y, int(value), ha="center", va="center",
                        color="white", fontsize=8, fontweight="bold")
        left += values
    ax.set_yticks([0, 1], labels=labels)
    ax.invert_yaxis()
    ax.set_xlabel("records, by worst severity reported")
    ax.set_title("Figure 4 — Does the checker fire on good data? (it does not)")
    ax.legend(frameon=False, ncol=4, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.3))
    ax.grid(axis="y", visible=False)
    return save(fig, "fig04_qc_dashboard.png")


def main() -> int:
    paths = [
        fig01_length_distribution(),
        fig02_composition_heatmap(),
        fig03_kmer_similarity(),
        fig04_qc_dashboard(),
    ]
    print(f"\n{len(paths)} figures written to {FIGURES.relative_to(REPO)}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
