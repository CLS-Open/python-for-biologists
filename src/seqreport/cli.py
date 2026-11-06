"""Command-line interface.

Design rules, all of them deliberate:

* **stdout is machine-readable, stderr is for humans.** ``--json`` output can be
  piped into ``jq`` without warning text corrupting it.
* **Exit codes mean something.** ``0`` pass, ``1`` the file has errors (the
  report was still produced), ``2`` the file could not be read at all. CI can
  therefore gate on the exit code.
* **No silent reformatting.** The tool never rewrites the input file.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .composition import composition, gc_content, gc_skew, at_skew, kmer_counts, molecular_weight, windowed_gc
from .qc import CheckOptions
from .records import FastaError, guess_molecule_type, parse_fasta, read_fasta
from .report import build_report, to_html, to_json, to_markdown


def _load(path: str) -> list:
    """Read a FASTA file, letting :class:`FastaError` reach :func:`main`.

    Error handling happens in exactly one place. An earlier version caught the
    error here *and* in ``main``, which meant the second handler was dead code
    and untestable — the kind of duplication that is invisible until something
    else needs to intercept the error.
    """
    return read_fasta(Path(path))


def _molecule_of(records, declared: str) -> str:
    if declared != "auto":
        return declared
    votes: dict[str, int] = {}
    for rec in records:
        kind = guess_molecule_type(rec.sequence)
        votes[kind] = votes.get(kind, 0) + 1
    return max(votes, key=lambda k: votes[k]) if votes else "unknown"


def _cmd_qc(args: argparse.Namespace) -> int:
    records = _load(args.file)
    opts = CheckOptions(
        molecule_type=args.molecule,
        min_length=args.min_length,
        max_ambiguous_fraction=args.max_ambiguous,
    )
    report = build_report(records, source=str(args.file), options=opts,
                          generated_by=f"seqreport {__version__}")
    if args.json:
        print(to_json(report))
    else:
        print(to_markdown(report), end="")
    return 1 if report.summary.errors else 0


def _cmd_stats(args: argparse.Namespace) -> int:
    records = _load(args.file)
    molecule = _molecule_of(records, args.molecule)
    rows = []
    for rec in records:
        row: dict[str, object] = {
            "id": rec.id,
            "length": len(rec.sequence),
            "molecule_type": guess_molecule_type(rec.sequence),
            "composition": composition(rec.sequence),
            "gc_skew": None,
            "at_skew": None,
            "gc": None,
            "molecular_weight_da": None,
        }
        if molecule == "nucleotide" or row["molecule_type"] == "nucleotide":
            try:
                row["gc"] = round(gc_content(rec.sequence), 6)
            except ValueError:
                row["gc"] = None
            row["gc_skew"] = gc_skew(rec.sequence)
            row["at_skew"] = at_skew(rec.sequence)
        else:
            try:
                row["molecular_weight_da"] = round(molecular_weight(rec.sequence, strict=False), 3)
            except ValueError:
                row["molecular_weight_da"] = None
        rows.append(row)

    if args.json:
        print(json.dumps({"file": str(args.file), "molecule_type": molecule, "records": rows}, indent=2))
        return 0

    print(f"{'id':<16} {'length':>7} {'type':<10} {'GC':>7} {'GC-skew':>8} {'AT-skew':>8} {'mass (Da)':>11}")
    for row in rows:
        gc = "—" if row["gc"] is None else f"{row['gc'] * 100:.1f}%"
        gcs = "—" if row["gc_skew"] is None else f"{row['gc_skew']:+.3f}"
        ats = "—" if row["at_skew"] is None else f"{row['at_skew']:+.3f}"
        mass = "—" if row["molecular_weight_da"] is None else f"{row['molecular_weight_da']:,.1f}"
        print(f"{row['id']:<16} {row['length']:>7} {row['molecule_type']:<10} {gc:>7} {gcs:>8} {ats:>8} {mass:>11}")
    print(f"\n{len(rows)} record(s); molecule type: {molecule}")
    return 0


def _cmd_windows(args: argparse.Namespace) -> int:
    records = _load(args.file)
    if args.record:
        matching = [r for r in records if r.id == args.record]
        if not matching:
            available = ", ".join(r.id for r in records[:8])
            print(f"error: no record with id {args.record!r}. Available: {available}", file=sys.stderr)
            return 2
        records = matching
    elif len(records) > 1:
        print(f"error: {args.file} has {len(records)} records; "
              "choose one with --record or split the file", file=sys.stderr)
        return 2
    windows = windowed_gc(records[0].sequence, window=args.window, step=args.step)
    payload = {"record": records[0].id, "window": args.window, "step": args.step or args.window,
               "windows": windows}
    if args.json:
        print(json.dumps(payload, indent=2))
        return 0
    print(f"{'start':>7} {'end':>7} {'GC':>7}")
    for w in windows:
        gc = "      —" if w["gc"] is None else f"{w['gc'] * 100:6.1f}%"
        print(f"{w['start']:>7} {w['end']:>7} {gc:>7}")
    return 0


def _cmd_kmers(args: argparse.Namespace) -> int:
    records = _load(args.file)
    if args.record:
        records = [r for r in records if r.id == args.record] or records[:1]
    counts = kmer_counts(records[0].sequence, k=args.k)
    total = sum(counts.values())
    top = list(counts.items())[: args.top]
    if args.json:
        print(json.dumps({"record": records[0].id, "k": args.k, "total": total,
                          "top": dict(top)}, indent=2))
        return 0
    print(f"{records[0].id}: k={args.k}, {total} k-mers, {len(counts)} distinct")
    for kmer, n in top:
        print(f"  {kmer}\t{n}\t{n / total:.3%}")
    return 0


def _cmd_report(args: argparse.Namespace) -> int:
    records = _load(args.file)
    opts = CheckOptions(molecule_type=args.molecule, min_length=args.min_length)
    report = build_report(records, source=str(args.file), options=opts,
                          generated_by=f"seqreport {__version__}")
    out = Path(args.out)
    if out.suffix.lower() in {".html", ".htm"}:
        out.write_text(to_html(report), encoding="utf-8")
    elif out.suffix.lower() in {".json"}:
        out.write_text(to_json(report), encoding="utf-8")
    elif out.suffix.lower() in {".md", ".markdown"}:
        out.write_text(to_markdown(report), encoding="utf-8")
    else:
        print(f"error: cannot infer format from {out.suffix!r}; use .html, .md or .json", file=sys.stderr)
        return 2
    print(f"wrote {out} ({out.stat().st_size:,} bytes) "
          f"— {report.summary.records} records, {report.summary.errors} error(s), "
          f"{report.summary.warnings} warning(s)", file=sys.stderr)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="seqreport",
        description="Quality control and composition reporting for FASTA files.",
    )
    parser.add_argument("--version", action="version", version=f"seqreport {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    def common(p: argparse.ArgumentParser) -> None:
        p.add_argument("file", help="FASTA file (.gz supported)")
        p.add_argument("--molecule", choices=["auto", "protein", "nucleotide"], default="auto")

    p = sub.add_parser("qc", help="check every record and report issues")
    common(p)
    p.add_argument("--min-length", type=int, default=20)
    p.add_argument("--max-ambiguous", type=float, default=0.10)
    p.add_argument("--json", action="store_true", help="emit JSON instead of Markdown")
    p.set_defaults(func=_cmd_qc)

    p = sub.add_parser("stats", help="composition table (GC, skew, molecular weight)")
    common(p)
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=_cmd_stats)

    p = sub.add_parser("windows", help="GC in sliding windows")
    common(p)
    p.add_argument("--window", type=int, default=50)
    p.add_argument("--step", type=int, default=None)
    p.add_argument("--record", default=None, help="record id (required for multi-record files)")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=_cmd_windows)

    p = sub.add_parser("kmers", help="most frequent k-mers")
    common(p)
    p.add_argument("--k", type=int, default=3)
    p.add_argument("--top", type=int, default=10)
    p.add_argument("--record", default=None)
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=_cmd_kmers)

    p = sub.add_parser("report", help="write an HTML/Markdown/JSON report")
    common(p)
    p.add_argument("--out", required=True)
    p.add_argument("--min-length", type=int, default=20)
    p.set_defaults(func=_cmd_report)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except FastaError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
