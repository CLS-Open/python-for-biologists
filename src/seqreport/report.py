"""Turning a checked file into something a reader can use.

Three renderings of one data structure — JSON, Markdown and a self-contained
HTML page. They are generated from the same :class:`RecordReport` objects, so
the HTML cannot disagree with the JSON (which is the usual way reports drift).

The HTML is deliberately dependency-free: inline CSS, no JavaScript, no external
fonts or images. It opens from a memory stick, survives being emailed, and does
not phone home when a student opens it.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from html import escape
from typing import Iterable, Sequence

from .composition import composition, gc_content, molecular_weight
from .qc import FILE_LEVEL_CODES, CheckOptions, Issue, Summary, check_records, summarise
from .records import Record

__all__ = [
    "RecordReport",
    "build_report",
    "to_json",
    "to_markdown",
    "to_html",
]


@dataclass
class RecordReport:
    """Everything known about one record after checking."""

    id: str
    description: str
    length: int
    molecule_type: str
    gc: float | None
    molecular_weight: float | None
    top_residues: list[tuple[str, int]]
    issues: list[Issue] = field(default_factory=list)

    def as_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "description": self.description,
            "length": self.length,
            "molecule_type": self.molecule_type,
            "gc": None if self.gc is None else round(self.gc, 6),
            "molecular_weight_da": None if self.molecular_weight is None else round(self.molecular_weight, 3),
            "top_residues": [{"residue": r, "count": c} for r, c in self.top_residues],
            "issues": [i.as_dict() for i in self.issues],
        }


@dataclass
class Report:
    """A whole file's report: summary plus one :class:`RecordReport` per record."""

    source: str
    generated_by: str
    options: dict[str, object]
    summary: Summary
    records: list[RecordReport]
    file_issues: list[Issue] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, object]:
        return {
            "source": self.source,
            "generated_by": self.generated_by,
            "options": self.options,
            "notes": list(self.notes),
            "summary": self.summary.as_dict(),
            "file_issues": [i.as_dict() for i in self.file_issues],
            "records": [r.as_dict() for r in self.records],
        }


def _top_residues(seq: str, n: int = 5) -> list[tuple[str, int]]:
    return list(composition(seq).items())[:n]


def build_report(records: Sequence[Record], *, source: str, options: CheckOptions | None = None,
                 generated_by: str = "seqreport", notes: Iterable[str] = ()) -> Report:
    """Check records and assemble a :class:`Report`.

    GC is only computed for records whose molecule type is guessed (or declared)
    as nucleotide; molecular weight only for proteins. Reporting a "GC content"
    for a protein, or a "molecular weight" computed from DNA letters with the
    protein mass table, is the kind of quietly wrong number this project refuses
    to emit, so the field is ``None`` instead.
    """
    opts = options or CheckOptions()
    issues = check_records(records, opts)
    by_record: dict[str, list[Issue]] = {}
    file_issues: list[Issue] = []
    for issue in issues:
        if issue.code in FILE_LEVEL_CODES:
            file_issues.append(issue)
        else:
            by_record.setdefault(issue.record_id, []).append(issue)

    rows: list[RecordReport] = []
    for rec in records:
        if opts.molecule_type == "auto":
            from .records import guess_molecule_type

            kind = guess_molecule_type(rec.sequence)
        else:
            kind = opts.molecule_type
        gc = None
        if kind == "nucleotide" and rec.sequence:
            try:
                gc = gc_content(rec.sequence)
            except ValueError:
                gc = None
        mass = None
        if kind == "protein" and rec.sequence:
            try:
                mass = molecular_weight(rec.sequence, strict=False)
            except ValueError:
                mass = None
        rows.append(
            RecordReport(
                id=rec.id,
                description=rec.description,
                length=len(rec.sequence),
                molecule_type=kind,
                gc=gc,
                molecular_weight=mass,
                top_residues=_top_residues(rec.sequence),
                issues=by_record.get(rec.id, []),
            )
        )

    return Report(
        source=source,
        generated_by=generated_by,
        options={
            "molecule_type": opts.molecule_type,
            "min_length": opts.min_length,
            "max_ambiguous_fraction": opts.max_ambiguous_fraction,
            "allow_duplicate_ids": opts.allow_duplicate_ids,
        },
        summary=summarise(records, issues),
        records=rows,
        file_issues=file_issues,
        notes=list(notes),
    )


def to_json(report: Report, *, indent: int = 2) -> str:
    """Serialise as JSON. ``None`` values are kept (they mean "not applicable")."""
    return json.dumps(report.as_dict(), indent=indent, ensure_ascii=False)


def _fmt(value: float | None, spec: str = ".3f") -> str:
    return "—" if value is None else format(value, spec)


def to_markdown(report: Report) -> str:
    """Render a GitHub-flavoured Markdown report, suitable for pasting in a PR."""
    s = report.summary
    lines = [
        f"# seqreport — {report.source}",
        "",
        f"Generated by `{report.generated_by}`. Molecule type: **{s.molecule_type}**.",
        "",
        "## Summary",
        "",
        "| Records | Residues | Errors | Warnings | Info | Records with no error or warning |",
        "|---:|---:|---:|---:|---:|---:|",
        f"| {s.records} | {s.residues} | {s.errors} | {s.warnings} | {s.info} | {s.clean_records} |",
        "",
        "## Records",
        "",
        "| id | length | type | GC | molecular weight (Da) | top residues |",
        "|---|---:|---|---:|---:|---|",
    ]
    for r in report.records:
        tops = ", ".join(f"{res}:{cnt}" for res, cnt in r.top_residues) or "—"
        lines.append(
            f"| `{r.id}` | {r.length} | {r.molecule_type} | {_fmt(r.gc * 100 if r.gc is not None else None, '.1f')}"
            f"{'' if r.gc is None else '%'} | {_fmt(r.molecular_weight, '.1f')} | {tops} |"
        )
    lines += ["", "## Issues", ""]
    if report.file_issues:
        lines += ["### File-level", "", "| severity | code | message |", "|---|---|---|"]
        for i in report.file_issues:
            lines.append(f"| {i.severity} | `{i.code}` | {i.message} |")
        lines.append("")
    if not any(r.issues for r in report.records):
        lines.append("No issues found. That is a statement about these checks, not about the data.")
    else:
        lines += ["| severity | code | record | message |", "|---|---|---|---|"]
        for r in report.records:
            for i in sorted(r.issues, key=lambda i: i.severity):
                lines.append(f"| {i.severity} | `{i.code}` | `{i.record_id}` | {i.message} |")
    if report.notes:
        lines += ["", "## Notes", ""] + [f"- {n}" for n in report.notes]
    return "\n".join(lines) + "\n"


_CSS = """
:root { color-scheme: light dark; }
body { font: 16px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
       margin: 0 auto; max-width: 60rem; padding: 2rem 1rem; }
h1 { font-size: 1.6rem; margin-bottom: .2rem; }
h2 { font-size: 1.2rem; margin-top: 2rem; border-bottom: 1px solid #8884; padding-bottom: .2rem; }
table { border-collapse: collapse; width: 100%; font-size: .9rem; }
th, td { text-align: left; padding: .3rem .5rem; border-bottom: 1px solid #8883; }
td.num, th.num { text-align: right; font-variant-numeric: tabular-nums; }
code { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: .9em; }
.sev-error { color: #b00020; font-weight: 600; }
.sev-warning { color: #8a5a00; }
.sev-info { color: #1b5e8a; }
.muted { color: #888; }
.cards { display: flex; gap: 1rem; flex-wrap: wrap; margin: 1rem 0; }
.card { border: 1px solid #8884; border-radius: 6px; padding: .6rem .9rem; min-width: 6rem; }
.card .n { font-size: 1.6rem; font-variant-numeric: tabular-nums; }
.card .k { font-size: .75rem; text-transform: uppercase; letter-spacing: .04em; color: #888; }
"""


def to_html(report: Report) -> str:
    """Render a single self-contained HTML page (inline CSS, no JavaScript)."""
    s = report.summary
    rows = []
    for r in report.records:
        gc = "—" if r.gc is None else f"{r.gc * 100:.1f}%"
        mass = "—" if r.molecular_weight is None else f"{r.molecular_weight:,.1f}"
        tops = " ".join(f"{escape(res)}{cnt}" for res, cnt in r.top_residues) or "—"
        rows.append(
            "<tr>"
            f"<td><code>{escape(r.id)}</code></td>"
            f'<td class="num">{r.length}</td>'
            f"<td>{escape(r.molecule_type)}</td>"
            f'<td class="num">{gc}</td>'
            f'<td class="num">{mass}</td>'
            f"<td>{escape(tops)}</td>"
            "</tr>"
        )
    issue_rows = [
        "<tr>"
        f'<td class="sev-{escape(i.severity)}">{escape(i.severity)}</td>'
        f"<td><code>{escape(i.code)}</code></td><td><em>file</em></td>"
        f"<td>{escape(i.message)}</td></tr>"
        for i in report.file_issues
    ]
    for r in report.records:
        for i in sorted(r.issues, key=lambda i: i.severity):
            issue_rows.append(
                "<tr>"
                f'<td class="sev-{escape(i.severity)}">{escape(i.severity)}</td>'
                f"<td><code>{escape(i.code)}</code></td>"
                f"<td><code>{escape(i.record_id)}</code></td>"
                f"<td>{escape(i.message)}</td>"
                "</tr>"
            )
    issues_html = (
        "<table><thead><tr><th>severity</th><th>code</th><th>record</th><th>message</th></tr></thead>"
        f"<tbody>{''.join(issue_rows)}</tbody></table>"
        if issue_rows
        else '<p class="muted">No issues found. That is a statement about these checks, not about the data.</p>'
    )
    notes_html = ""
    if report.notes:
        notes_html = "<h2>Notes</h2><ul>" + "".join(f"<li>{escape(n)}</li>" for n in report.notes) + "</ul>"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>seqreport — {escape(report.source)}</title>
<style>{_CSS}</style>
</head>
<body>
<h1>seqreport</h1>
<p class="muted"><code>{escape(report.source)}</code> · molecule type
<strong>{escape(s.molecule_type)}</strong> · generated by <code>{escape(report.generated_by)}</code></p>
<div class="cards">
  <div class="card"><div class="n">{s.records}</div><div class="k">records</div></div>
  <div class="card"><div class="n">{s.residues:,}</div><div class="k">residues</div></div>
  <div class="card"><div class="n sev-error">{s.errors}</div><div class="k">errors</div></div>
  <div class="card"><div class="n sev-warning">{s.warnings}</div><div class="k">warnings</div></div>
  <div class="card"><div class="n sev-info">{s.info}</div><div class="k">info</div></div>
  <div class="card"><div class="n">{s.clean_records}/{s.records}</div><div class="k">clean</div></div>
</div>
<h2>Records</h2>
<table>
<thead><tr><th>id</th><th class="num">length</th><th>type</th><th class="num">GC</th>
<th class="num">molecular weight (Da)</th><th>top residues</th></tr></thead>
<tbody>{''.join(rows)}</tbody>
</table>
<h2>Issues</h2>
{issues_html}
{notes_html}
<p class="muted">Generated from the same data structure as the JSON and Markdown renderings,
so the three agree by construction. Checks are a fixed rule set — not a review.</p>
</body>
</html>
"""
