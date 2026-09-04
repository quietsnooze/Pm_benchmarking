# Appendix — detailed data provenance

Raw figures behind the processed datasets, captured with source, unit, period
and definition so every derived number can be re-checked against the primary
document. Amounts are as printed in the source (currency and unit stated per
block). This appendix is committed; the source PDFs live in `raw_inputs/`
(gitignored, reproducible from the URLs in [SOURCES.md](SOURCES.md)).

---

## Mortgage & unsecured-retail provision coverage (annual reports)

Feeds `processed_inputs/firm_provisions_annual_reports.csv`. **Coverage =
impairment allowance (balance-sheet stock) ÷ gross loans, per product**, at
the test's start point (31 December of the year before the ACS; Nationwide
uses its nearest 4 April year-end). Numerator and denominator are captured
separately so the ratio is re-derivable.

Product definitions (applied consistently):

- **mortgage** — UK residential mortgages.
- **unsecured_retail** — credit cards + personal loans + overdrafts (excludes
  auto/motor and any secured lending).
- Commercial is out of scope here (sourced from the EBA file; see SOURCES.md).

Accounting basis: **IAS 39** (incurred loss) for FY2017 and earlier;
**IFRS 9** (expected credit loss) from FY2018. The two are not comparable
across the 1 Jan 2018 transition — every IAS 39 → IFRS 9 step is flagged.

Entity: group level, to match the rest of the dataset, except where only a
ring-fenced UK sub (e.g. HSBC UK Bank plc, Barclays Bank UK PLC, both from
2018) discloses the UK product split — then the sub is used and named in the
`entity` column.

### Lloyds Banking Group

**FY2018 → 2019 ACS** (balance-sheet date 31 December 2018). Basis: IFRS 9.
Entity: Lloyds Banking Group (group). Currency: GBP millions.
Source: [LBG Annual Report 2018](https://www.lloydsbankinggroup.com/assets/pdfs/investors/annual-report/2018-download-links/2018_lbg_annual_report.pdf),
Risk management — Retail credit risk, **underlying basis**.

Underlying basis is used because it carries the per-segment gross lending
(Table 1.10a) and per-segment ECL allowance (Table 1.11a) on the same IFRS 9
footing, so coverage is exactly re-derivable and matches Lloyds' own printed
ratios; it also strips the HBOS/MBNA acquisition-accounting distortions
(purchased-or-originated-credit-impaired assets) that make the statutory
figures hard to compare year on year. The statutory-basis allowances are
noted alongside for reference.

| Product | Segment (report label) | Gross lending £m | ECL allowance £m | Coverage | Source |
| --- | --- | --- | --- | --- | --- |
| mortgage | Secured | 289,237 | 1,462 | 0.5055% | Table 1.10a (gross, p124) / Table 1.11a (allowance, p126) |
| unsecured_retail | Unsecured | 27,990 | 980 | 3.5013% | Table 1.10a (gross, p124) / Table 1.11a (allowance, p126) |

Notes:
- "Secured" (Retail division) is UK residential mortgages; reproduces Lloyds'
  printed coverage of 0.5%.
- "Unsecured" is *Credit cards, Loans and Overdrafts* (report footnote 2) —
  matches the unsecured-retail definition exactly; UK Motor Finance is a
  separate segment and is excluded. Reproduces printed coverage of 3.5%.
- Statutory-basis ECL allowances (Table 1.11, p126) for reference: Secured
  £460m, Unsecured £896m.
- Cross-check: the static FY2019-vintage snapshot `firm_provisions.csv` has
  Lloyds mortgage 0.4% and retail 3.8% — same order of magnitude.
