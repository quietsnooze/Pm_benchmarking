"""Extract bank-specific projected impairment-charge tables from BoE results PDFs.

The Bank of England's annual stress-test results PDFs (2014–2017 in
``raw_inputs/``) each end with an annex titled something like *"Bank-specific
projected impairment charges and traded risk losses"* (2014 calls it *"firm-
specific"*; 2017 promotes it to *"Annex 5"*). This module locates that annex,
parses each ``Table <id>`` block within it, and writes one CSV per table to
``processed_inputs/``, plus an ``_index.csv`` summarising what was extracted.

Public surface:
    extract_appendix_tables(pdf_path, out_dir) -> ExtractReport
    parse_table_block(lines) -> ParsedTable | None

Limitations of v1:
- Column headers in the source PDFs are typeset across multiple lines and
  occasionally two-level (super-header + sub-header). PDF text extraction
  flattens this in unpredictable ways, so output CSVs use placeholder column
  names ``col_1``, ``col_2``, ..., and the raw header lines from the PDF are
  recorded in ``_index.csv`` for any later cleanup.
- Numeric values are written as strings to preserve the original formatting
  (including ``-`` for "not applicable" and any percentage suffixes).
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field
from pathlib import Path

import pdfplumber

# Firms whose names anchor data rows. Sorted longest-first so the prefix
# matcher picks "The Royal Bank of Scotland Group" over the bare bank name.
_FIRMS = [
    "The Royal Bank of Scotland Group",
    "The Royal Bank of Scotland",
    "The Co-operative Bank",
    "Lloyds Banking Group",
    "Standard Chartered",
    "Santander UK Group Holdings plc",
    "Santander UK",
    "Nationwide Building Society",
    "Nationwide",
    "Barclays plc",
    "Barclays",
    "HSBC Holdings plc",
    "HSBC",
    "Co-op",
]
_FIRM_RE = re.compile(
    r"^(?P<firm>" + "|".join(re.escape(f) for f in _FIRMS) + r")(?:\s+(?P<rest>.*))?$"
)

# Annex heading we look for. Matches both 2014's "FIRM-SPECIFIC" variant and
# the "bank-specific" wording used 2015 onwards.
_ANNEX_RE = re.compile(r"(?i)(?:bank|firm)-specific projected impairment charges")

# Table title: "Table 1: ..." (2014), "Table 2A ..." (2015/16),
# "Table A5.C ..." (2017). Captures the id (alphanumerics + dot) and title.
_TABLE_TITLE_RE = re.compile(r"^Table\s+(?P<id>[A-Z0-9.]+)[:\s]+(?P<title>.+)$")

# Unit line directly under the title (2015+). 2014 has no separate unit line.
_UNIT_RE = re.compile(
    r"^(?:Per\s+cent|£\s*billions?|\$\s*billions?|US\$\s*billions?)\s*$",
    re.IGNORECASE,
)

# End-of-table markers: "Sources:" / "Source:" or footnote markers like "(a)".
_END_OF_TABLE_RE = re.compile(r"^(?:Sources?:|\([a-z]\))", re.IGNORECASE)

_GLOSSARY_RE = re.compile(r"(?i)^glossary\b")


@dataclass
class ParsedTable:
    table_id: str
    title: str
    unit: str
    raw_header_lines: list[str]
    rows: list[tuple[str, ...]]  # (firm, val1, val2, ...)


@dataclass
class ExtractReport:
    csv_paths: list[Path] = field(default_factory=list)
    tables: list[ParsedTable] = field(default_factory=list)


def _normalise(text: str) -> str:
    # pdfplumber occasionally yields the Unicode replacement char in place of
    # the £ sign (font-encoding quirk). Restore it; the symbol only matters
    # in unit lines and footnotes.
    return text.replace("�", "£")


def parse_table_block(lines: list[str]) -> ParsedTable | None:
    """Parse the lines of a single table block into a ``ParsedTable``.

    The first line must match a ``Table <id>: ...`` header. Subsequent lines
    are walked: the unit line (if present) is captured, then header text
    accumulates until the first firm-anchored data row; data rows continue
    until a ``Sources:`` or ``(a)`` footnote line ends the block.
    """
    if not lines:
        return None
    title_match = _TABLE_TITLE_RE.match(lines[0].strip())
    if not title_match:
        return None
    table_id = title_match.group("id").rstrip(".")
    title = title_match.group("title").strip()

    unit = ""
    header_lines: list[str] = []
    rows: list[tuple[str, ...]] = []

    for raw in lines[1:]:
        line = raw.strip()
        if not line:
            continue
        if _END_OF_TABLE_RE.match(line):
            break
        if not rows and _UNIT_RE.match(line):
            unit = line
            continue
        firm_match = _FIRM_RE.match(line)
        if firm_match:
            firm = firm_match.group("firm")
            rest = (firm_match.group("rest") or "").strip()
            values = tuple(re.split(r"\s+", rest)) if rest else ()
            rows.append((firm, *values))
            continue
        # Treat anything before the first data row as part of the header
        if not rows:
            header_lines.append(line)
    return ParsedTable(
        table_id=table_id,
        title=title,
        unit=unit,
        raw_header_lines=header_lines,
        rows=rows,
    )


def _find_annex_start(pages: list[str]) -> int | None:
    """Return the page index where the impairment-charges annex *begins*.

    The phrase appears earlier in the document too (table of contents,
    executive summary), so we want the *last* page that matches — that's the
    real section heading. Earlier matches are TOC entries.
    """
    last_match: int | None = None
    for i, page_text in enumerate(pages):
        if _ANNEX_RE.search(page_text):
            last_match = i
    return last_match


def _split_into_table_blocks(pages_after_annex: list[str]) -> list[list[str]]:
    """Walk the annex pages and group lines into one block per ``Table <id>``."""
    blocks: list[list[str]] = []
    current: list[str] | None = None
    for page_text in pages_after_annex:
        for raw in page_text.splitlines():
            line = raw.strip()
            if _GLOSSARY_RE.match(line):
                if current is not None:
                    blocks.append(current)
                return blocks
            if _TABLE_TITLE_RE.match(line):
                if current is not None:
                    blocks.append(current)
                current = [line]
            elif current is not None:
                current.append(raw)
    if current is not None:
        blocks.append(current)
    return blocks


def _year_from_pdf(pdf_path: Path) -> str:
    match = re.search(r"(\d{4})", pdf_path.stem)
    return match.group(1) if match else "unknown"


def _safe_table_id(table_id: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "", table_id) or "x"


def _write_table_csv(table: ParsedTable, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    n_value_cols = max((len(row) - 1 for row in table.rows), default=0)
    header = ["firm"] + [f"col_{i + 1}" for i in range(n_value_cols)]
    with out_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(header)
        for row in table.rows:
            padded = list(row) + [""] * (len(header) - len(row))
            writer.writerow(padded[: len(header)])


def extract_appendix_tables(pdf_path: Path, out_dir: Path) -> ExtractReport:
    """Extract bank-specific impairment-charge tables from one BoE results PDF."""
    year = _year_from_pdf(pdf_path)
    with pdfplumber.open(pdf_path) as pdf:
        pages = [_normalise(page.extract_text() or "") for page in pdf.pages]
    start = _find_annex_start(pages)
    if start is None:
        return ExtractReport()
    blocks = _split_into_table_blocks(pages[start:])

    report = ExtractReport()
    for block in blocks:
        table = parse_table_block(block)
        if table is None or not table.rows:
            continue
        out_path = out_dir / f"{year}_table-{_safe_table_id(table.table_id)}.csv"
        _write_table_csv(table, out_path)
        report.csv_paths.append(out_path)
        report.tables.append(table)
    return report


def _write_index(
    runs: list[tuple[Path, ExtractReport]],
    out_dir: Path,
) -> Path:
    index_path = out_dir / "_index.csv"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    with index_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["year", "table_id", "output_csv", "title", "unit", "raw_header"])
        for pdf_path, report in runs:
            year = _year_from_pdf(pdf_path)
            for table, csv_path in zip(report.tables, report.csv_paths, strict=True):
                writer.writerow(
                    [
                        year,
                        table.table_id,
                        csv_path.name,
                        table.title,
                        table.unit,
                        " / ".join(table.raw_header_lines),
                    ]
                )
    return index_path


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    raw_dir = repo_root / "raw_inputs"
    out_dir = repo_root / "processed_inputs"
    pdfs = sorted(raw_dir.glob("stress-testing-the-uk-banking-system-*-results.pdf"))
    if not pdfs:
        print(f"No matching results PDFs in {raw_dir}")
        return
    runs: list[tuple[Path, ExtractReport]] = []
    for pdf in pdfs:
        report = extract_appendix_tables(pdf, out_dir)
        runs.append((pdf, report))
        print(f"{pdf.name}: extracted {len(report.csv_paths)} table(s)")
    index_path = _write_index(runs, out_dir)
    total = sum(len(r.csv_paths) for _, r in runs)
    print(f"Total: {total} table(s) -> {out_dir.relative_to(repo_root)}")
    print(f"Index: {index_path.relative_to(repo_root)}")


if __name__ == "__main__":
    main()
