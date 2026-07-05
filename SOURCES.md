# Data sources

Raw source files for `raw_inputs/` are kept locally only (gitignored). This file records where each one came from so the workspace can be reconstructed on a fresh machine. Update it whenever a raw file is added or replaced.

The **[Verified direct URLs](#verified-direct-urls)** section near the bottom is machine-readable: running `python -m uk_stress_benchmark.sync_sources` parses each `` - `filename` -> <url> `` bullet and downloads any file not already present in `raw_inputs/`. Catalogue tables above are documentation only — extend them when you need a place to record provenance, but the downloader only reads the verified-URLs list.

## Bank of England — concurrent stress-test scenarios

Published annually alongside the BoE concurrent stress-test exercise. Source: bankofengland.co.uk, "Stress testing" section.

| Filename | Year | Notes |
| --- | --- | --- |
| `stress-testing-the-uk-banking-system-variable-paths-for-the-2014-scenario.xlsx` | 2014 | ACS scenario macro variable paths |
| `stress-testing-the-uk-banking-system-variable-paths-for-the-2015-scenario.xlsx` | 2015 | |
| `variable-paths-for-the-2016-stress-test.xlsx` | 2016 | naming changed for 2016 only |
| `stress-testing-the-uk-banking-system-variable-paths-for-the-2017-scenario.xlsx` | 2017 | |
| `stress-testing-the-uk-banking-system-variable-paths-for-the-2018-scenario.xlsx` | 2018 | |
| `stress-testing-the-uk-banking-system-variable-paths-for-the-2019-scenario.xlsx` | 2019 | |
| `variable-paths-for-firms-not-participating-in-2019-concurrent-stress-test.XLSX` | 2019 | Non-participating firms |
| `stress-testing-the-uk-banking-system-2014-results.pdf` … `-2017-results.pdf` | 2014–2017 | Annual results commentaries |
| `november-2018.pdf` | 2018 | BoE Financial Stability Report (containing 2018 stress-test results) |
| `december-2019.pdf` | 2019 | BoE FSR with 2019 stress-test results |
| `effectiveness-of-stresstesting-model-risk-management.pdf` | — | BoE paper on stress-testing model risk management — exact publication not yet identified |
| `mortgages-estimating-default-correlation-and-forecasting-default-risk.pdf` | 2018 | BoE Staff Working Paper No. 708 |

## European Banking Authority — EU-wide stress test & transparency exercise

Source: eba.europa.eu, "Risk analysis and data" / EU-wide stress-test results pages.

| Filename | Year | Notes |
| --- | --- | --- |
| `Credit Risk_Aggregates by Counterparty_2018.xlsb` (+ `.xlsx` export) | 2018 | EBA stress-test aggregates |
| `Credit Risk_Individual Banks_2018 2.xlsb` (+ `.xlsx` export) | 2018 | Per-bank disclosures |
| `TRA_CR.csv` | 2018 | EU-wide Transparency Exercise — credit risk |
| `TRA_OTH.csv` | 2018 | EU-wide Transparency Exercise — other |
| `Data Dictionary.xlsx` | 2018 | Field definitions for the above |
| `EBA_ST_UK_549300PPXHEU2JF0AM85.pdf` | — | UK-bank summary (LEI in filename) |

## Federal Reserve — DFAST

Source: federalreserve.gov, supervisory stress-test publications.

| Filename | Notes |
| --- | --- |
| `public_results_DFAST.csv` | Compiled DFAST public results |

## FCA — Product Sales Data

Source: fca.org.uk, Product Sales Data publications.

| Filename | Notes |
| --- | --- |
| `psd-mortgages-2018.xlsx` | FCA PSD mortgages, 2018 |

## Firm Pillar 3 disclosures and annual reports

Each firm publishes its own. Source: investor-relations pages of the relevant firm.

| Filename | Firm | Notes |
| --- | --- | --- |
| `2014_lbg_fy_results_excel_download_updated.numbers` | Lloyds Banking Group | FY 2014 results |
| `2019 provisions coverage by firm.xlsx` | (compilation) | Provisions coverage extracted from multiple firms' Pillar 3 |
| `hsbc ltv calculator.xlsx` | HSBC | LTV calculator |
| `standard-chartered-plc-full-year-2019-data-pack.xlsx` | Standard Chartered | FY 2019 data pack |

## Verified direct URLs

The downloader (`python -m uk_stress_benchmark.sync_sources`) parses the bullet list below. Each line of the form ``- `filename.ext` -> <https://...>`` is treated as a directive to ensure that filename exists at `raw_inputs/<filename>`. Adding entries here is how new files get auto-fetched.

- `stress-testing-the-uk-banking-system-2014-results.pdf` → <https://www.bankofengland.co.uk/-/media/boe/files/stress-testing/2014/stress-testing-the-uk-banking-system-2014-results.pdf>
- `stress-testing-the-uk-banking-system-2015-results.pdf` → <https://www.bankofengland.co.uk/-/media/boe/files/stress-testing/2015/stress-testing-the-uk-banking-system-2015-results.pdf>
- `stress-testing-the-uk-banking-system-2016-results.pdf` → <https://www.bankofengland.co.uk/-/media/boe/files/stress-testing/2016/stress-testing-the-uk-banking-system-2016-results.pdf>
- `stress-testing-the-uk-banking-system-2017-results.pdf` → <https://www.bankofengland.co.uk/-/media/boe/files/stress-testing/2017/stress-testing-the-uk-banking-system-2017-results.pdf>
- `stress-testing-the-uk-banking-system-variable-paths-for-the-2014-scenario.xlsx` → <https://www.bankofengland.co.uk/-/media/boe/files/stress-testing/2014/stress-testing-the-uk-banking-system-variable-paths-for-the-2014-scenario.xlsx>
- `stress-testing-the-uk-banking-system-variable-paths-for-the-2015-scenario.xlsx` → <https://www.bankofengland.co.uk/-/media/boe/files/stress-testing/2015/stress-testing-the-uk-banking-system-variable-paths-for-the-2015-scenario.xlsx>
- `variable-paths-for-the-2016-stress-test.xlsx` → <https://www.bankofengland.co.uk/-/media/boe/files/stress-testing/2016/variable-paths-for-the-2016-stress-test.xlsx>
- `stress-testing-the-uk-banking-system-variable-paths-for-the-2017-scenario.xlsx` → <https://www.bankofengland.co.uk/-/media/boe/files/stress-testing/2017/stress-testing-the-uk-banking-system-variable-paths-for-the-2017-scenario.xlsx>
- `stress-testing-the-uk-banking-system-variable-paths-for-the-2018-scenario.xlsx` → <https://www.bankofengland.co.uk/-/media/boe/files/stress-testing/2018/stress-testing-the-uk-banking-system-variable-paths-for-the-2018-scenario.xlsx>
- `stress-testing-the-uk-banking-system-variable-paths-for-the-2019-scenario.xlsx` → <https://www.bankofengland.co.uk/-/media/boe/files/stress-testing/2019/stress-testing-the-uk-banking-system-variable-paths-for-the-2019-scenario.xlsx>
- `variable-paths-for-firms-not-participating-in-2019-concurrent-stress-test.XLSX` → <https://www.bankofengland.co.uk/-/media/boe/files/stress-testing/2019/variable-paths-for-firms-not-participating-in-2019-concurrent-stress-test.xlsx>
- `stress-testing-the-uk-banking-system-variable-paths-for-the-2021-scenario.xlsx` → <https://www.bankofengland.co.uk/-/media/boe/files/stress-testing/2021/variable-paths-for-the-2021-stress-test.xlsx>
- `stress-testing-the-uk-banking-system-variable-paths-for-the-2022-scenarios.xlsx` → <https://www.bankofengland.co.uk/-/media/boe/files/stress-testing/2023/variable-paths-for-the-2022-scenarios.xlsx>
- `variable-paths-for-the-2025-bank-capital-stress-test.xlsx` → <https://www.bankofengland.co.uk/-/media/boe/files/stress-testing/2025/variable-paths-for-the-2025-bank-capital-stress-test.xlsx>
- `november-2018.pdf` → <https://www.bankofengland.co.uk/-/media/boe/files/financial-stability-report/2018/november-2018.pdf>
- `december-2019.pdf` → <https://www.bankofengland.co.uk/-/media/boe/files/financial-stability-report/2019/december-2019.pdf>
- `mortgages-estimating-default-correlation-and-forecasting-default-risk.pdf` → <https://www.bankofengland.co.uk/-/media/boe/files/working-paper/2018/mortgages-estimating-default-correlation-and-forecasting-default-risk.pdf>

### URL not yet identified

Files referenced in the legacy folder for which the corresponding BoE publication has not been confirmed. The downloader skips these (no URL on the line):

- `effectiveness-of-stresstesting-model-risk-management.pdf` — likely either SS3/18 *Model risk management principles for stress testing* (PRA, 2018) or a renamed copy of the 2019 *Effectiveness of stress testing framework and its implementation* paper. To resolve, open the local PDF and check its title/cover page.

## Local-only data (not downloadable)

These files have no public URL — they're hand-compiled summaries Pete put together from individual firms' Pillar 3 / annual-report disclosures. The transcribed CSVs in `processed_inputs/` are the committed source of truth; the source XLSXs live only in `old_version/` (gitignored) on Pete's machine.

| Source XLSX | Transcription script | Output CSV | Provides |
| --- | --- | --- | --- |
| `old_version/stress test benchmarks/pillar 3 disclosures/2019 provisions coverage by firm.xlsx` | [scripts/derive_firm_provisions.py](scripts/derive_firm_provisions.py) | `processed_inputs/firm_provisions.csv` | `firm_name`, `mort_prov_coverage`, `retail_prov_coverage`, `commercial_prov_coverage` for each of the seven UK banks. SCB has only `commercial_prov_coverage` populated (a flagged "guesstimate" in the source). |

### `processed_inputs/firm_btl.csv` — buy-to-let share of mortgage book

`firm_name`, `btl_share` — buy-to-let balances as a fraction of each firm's UK
mortgage book. A **single static figure per firm**, applied across every
stress-test year (deliberately, per the design brief: BTL mix moves slowly, so
one point is a workable starting proxy rather than tracking it test-by-test).
Authored directly as a committed CSV (no legacy XLSX, hence no `derive_*`
script); loaded by `uk_stress_benchmark.provisions.load_btl` and used only by
the mortgage model.

> **⚠️ Provisional — verify before public launch.** Only Santander UK (~9%,
> stated as stable year-on-year in its 2025 reporting) is confirmed from a
> primary source. The remaining figures are approximate placeholders set to the
> well-established *relative* BTL intensity of each lender (HSBC UK lowest as a
> late/small BTL entrant; Nationwide via The Mortgage Works and Lloyds via
> Birmingham Midshires among the highest). They should be replaced with exact
> figures from each firm's annual report / Pillar 3 disclosure. Standard
> Chartered is left blank (no UK mortgage book; excluded from modelling anyway).

| Firm | `btl_share` | Basis |
| --- | --- | --- |
| Santander UK | 0.09 | Confirmed ~9%, stable YoY (Santander UK 2025 reporting). |
| Lloyds Banking Group | 0.13 | Placeholder — large BTL lender (Birmingham Midshires / BM Solutions). |
| Nationwide | 0.15 | Placeholder — largest relative BTL via The Mortgage Works (TMW). |
| NatWest / RBS Group | 0.11 | Placeholder — moderate BTL book. |
| Barclays | 0.10 | Placeholder — moderate BTL book. |
| HSBC | 0.02 | Placeholder — minimal BTL (entered the market late, small book). |
| Standard Chartered | (blank) | No UK mortgage book; excluded from modelling. |

### 2021 Solvency Stress Test — scenario only (not a training year)

The 2021 SST *scenario* is ingested (`scenario-2021-stress.csv`, in the manifest)
for what-if / coverage, but its bank-specific results are **deliberately not
pooled into the regression**: the 2021 SST is a COVID-recovery scenario whose
milder path destabilises the pooled fit, so by decision it is scenario-only.
Hence there is no `2021_table-*.csv`. (For the record, the results exist as
Annex 2 Table A2.A of the *2021 solvency stress test results: annex*, same
four-product shape as the other years.) Note the 2021 SST scenario is a single
severe macro path — not the 2021 Climate Biennial Exploratory Scenario, which
is a separate exercise with EA/LA/NAA pathways.

### 2022/23 ACS — bank-specific impairment charges

`processed_inputs/2022_table-A2A.csv` was transcribed from **Annex 2, Table
A2.A** of the *2022/23 ACS stress-test results: Annex* (finalised 11 July 2023).
Only the seven group-level firms are kept; the ring-fenced subsidiaries
(Barclays Bank UK, HSBC UK Bank) and standalone Virgin Money UK are dropped to
match the legacy 2014-2019 group-level firm set. Same `firm, col_1..col_4`
shape and four products as the legacy tables. `NatWest Group` is canonicalised
to `The Royal Bank of Scotland Group`. Transcribed (not `extract-tables`-parsed)
because the new annex layout differs from the 2014-2019 annex the extractor
understands; see the follow-up to extend `extract-tables` to the A2/A3 annexes.

### 2025 Bank Capital Stress Test — bank-specific impairment charges

`processed_inputs/2025_table-A31.csv` was transcribed by hand from **Annex 3,
Table A3.1** ("Projected cumulative five-year impairment charge rates on UK
lending in the stress scenario") of the 2 December 2025 *Bank Capital Stress
Test results* annex. It is kept in the same `firm, col_1..col_4` shape the
`extract-tables` step produces (mortgage / non-mortgage retail / CRE / business
excluding CRE), so `aggregate-firm-results` picks it up like any other year.

Transcribed rather than extracted because the annex PDF would not download at
build time; if the PDF (`...2025...bank-capital-stress-test...annex.pdf`) is
later obtained, add it to the verified-URLs list and let `extract-tables`
regenerate the CSV to confirm the transcription. Per the annex's own footnote,
the "Nationwide" figures include Virgin Money UK heritage, and "NatWest Group"
is canonicalised to "The Royal Bank of Scotland Group" for cross-era continuity.

## TBD — origin not confirmed

These appeared in the legacy folder; original source is not recorded. Pete to fill in:

- `eco_scenarios_low_point.csv` — possibly a derived intermediate, not a raw source.
- `results.csv` / `results.numbers` — firm-level impairment-charge percentages keyed by ACS year. Likely manually compiled from the BoE results PDFs above; confirm.
