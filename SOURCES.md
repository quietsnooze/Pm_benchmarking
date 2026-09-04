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
- `eba-transparency-2020-tr_cre.csv` → <https://www.eba.europa.eu/sites/default/files/document_library/Risk%20Analysis%20and%20Data/EU%20Wide%20Transparency%20Exercise/2020/Full%20database/885657/tr_cre.csv>

### URL not yet identified

Files referenced in the legacy folder for which the corresponding BoE publication has not been confirmed. The downloader skips these (no URL on the line):

- `eba-transparency-2015-tr_cre.csv` — credit-risk CSV from the 2015 EU-wide transparency exercise "Full database" download. Grab it from the 2015 landing page listed under *Provision coverage by firm — annual sources* below; the URL path contains a numeric folder that search did not surface.
- `eba-transparency-2016-tr_cre.csv` — credit-risk CSV from the 2016 EU-wide transparency exercise "Full database" download. Grab it from the 2016 landing page listed under *Provision coverage by firm — annual sources* below; the URL path contains a numeric folder that search did not surface.
- `eba-transparency-2017-tr_cre.csv` — credit-risk CSV from the 2017 EU-wide transparency exercise "Full database" download. Grab it from the 2017 landing page listed under *Provision coverage by firm — annual sources* below; the URL path contains a numeric folder that search did not surface.
- `eba-transparency-2018-tr_cre.csv` — credit-risk CSV from the 2018 EU-wide transparency exercise "Full database" download. Grab it from the 2018 landing page listed under *Provision coverage by firm — annual sources* below; the URL path contains a numeric folder that search did not surface.
- `eba-transparency-2019-tr_cre.csv` — credit-risk CSV from the 2019 EU-wide transparency exercise "Full database" download. Grab it from the 2019 landing page listed under *Provision coverage by firm — annual sources* below; the URL path contains a numeric folder that search did not surface.
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

## Provision coverage by firm — annual sources

`processed_inputs/firm_provisions.csv` is a single 2019 snapshot per firm and
is what the app and the regression use. The annual counterpart,
`processed_inputs/firm_provisions_annual.csv` (one row per firm × ACS year,
plus an `acsyear` column), is built by `uv run extract-provisions` from the
EBA transparency-exercise files listed below; it is committed as a data asset
but carries commercial coverage only (see product mapping below) and isn't
wired into the app yet — wiring its commercial column in as a per-year
overlay on top of the static file is a planned follow-up. Coverage means the
**stock** of provisions ÷ gross exposure by product at the test's start point
(31 December of the year before the ACS) — not the impairment *charge*.

### Primary: EBA EU-wide Transparency Exercise (2015–2020 exercises)

The only standardised, machine-readable, bank-by-bank source found. The
credit-risk file (`tr_cre.csv`, one per exercise) carries "Original Exposure"
and "Value adjustments and provisions" by exposure class, portfolio (SA / IRB),
counterparty country and reference period. UK banks are in the sample up to the
**spring 2020** exercise (last data point 31 Dec 2019); from the 2021 exercise
they are absent (post-Brexit), so 2022 and 2025 tests need the fallback below.

| ACS year | Start point | Exercise | `raw_inputs/` filename | `Period` | Download URL |
| --- | --- | --- | --- | --- | --- |
| 2014 | 31 Dec 2013 | — (2013 exercise stops at Jun 2013; the 2014 EU-wide *stress test* templates carry Dec 2013 credit-risk data — unverified) | — | — | not covered |
| 2015 | 31 Dec 2014 | 2015 | `eba-transparency-2015-tr_cre.csv` | 201412 | not yet identified (see below) |
| 2016 | 31 Dec 2015 | 2016 | `eba-transparency-2016-tr_cre.csv` | 201512 | not yet identified |
| 2017 | 31 Dec 2016 | 2017 | `eba-transparency-2017-tr_cre.csv` | 201612 | not yet identified |
| 2018 | 31 Dec 2017 | 2018 | `eba-transparency-2018-tr_cre.csv` | 201712 | not yet identified |
| 2019 | 31 Dec 2018 | 2019 | `eba-transparency-2019-tr_cre.csv` | 201812 | not yet identified |
| (none) | 31 Dec 2019 | spring 2020 | `eba-transparency-2020-tr_cre.csv` | 201912 | **verified** — in the verified-URLs list |

The 2020 file has no matching ACS but is kept in the manifest: it is the only
file whose URL was seen verbatim, so it is the real-data smoke test for the
parser, and it gives the app each firm's most recent coverage.

**Firms in the sample** (LEIs used by the extractor): Barclays
(`G5GSEF7VJP5I7OUK5573`, Barclays Bank PLC — the LEI the 2018 files used;
`213800LBQA1Y9L22JB70`, Barclays PLC, also mapped in case later files switched),
HSBC Holdings (`MLU0ZO3ML4LN2LL2TL39`), Lloyds (`549300PPXHEU2JF0AM85`), RBS /
NatWest (`2138005O9XJIJN4JPN90`), Nationwide (`549300XFX12G42QIKN82`), Standard
Chartered (`U4LOSYZ7YG4W3S5F2G91`). **Santander UK** is consolidated into
Banco Santander SA (`5493006QMFDDMYWIAM13`) in the exercise, so its book is
recovered as Banco Santander's UK (Country 30) slice, on the same
group-UK-geography basis as every other firm. Santander UK plc's own LEI
(`PTCQB104N23FMNK2RZ28`) is also mapped for the unlikely case it ever files
separately; confirmed against the 2020 file, only the Banco Santander LEI
appears. The Banco Santander slice is mostly Santander UK plc but may include
other UK lending booked elsewhere in the group — a small, acceptable
difference given the whole panel is group-UK-geography, flagged here for the
record.

**Country handling.** Each firm uses its UK-counterparty rows (Country 30 /
`GB`). A UK-only lender reports no geographic breakdown — Nationwide files
its whole book under Country 0 (total) — so the extractor falls back to a
firm's all-countries total when, and only when, it has no UK-geography rows
at all. A diversified group keeps its UK slice; its global total is never
counted as UK.

**Product mapping — commercial only (option A).** Real 2020 data showed
that IRB banks (e.g. Lloyds) report retail exposure under one aggregate
"Retail" exposure class (404) and do not break out mortgages (406) or
unsecured retail (409/410), so those two products cannot be separated from
this file. Commercial (Corporates, 303) *is* clean under both SA and IRB
reporting, so the extractor sums SA + IRB Corporates (`Status` 0 =
defaulted + non-defaulted together; "of which" sub-rows excluded to avoid
double counting) into `commercial_prov_coverage`. `mort_prov_coverage` and
`retail_prov_coverage` always come back NaN from this route by design — an
honest placeholder, not a blended or zero number — and stay sourced from
the annual-report route (the static `firm_provisions.csv`) instead.

| Product column | IRB exposure classes | SA exposure classes |
| --- | --- | --- |
| `commercial_prov_coverage` | 303 Corporates | 303 Corporates |

**Caveats.**

- The parser was validated against synthetic fixtures only: the build sandbox
  could not reach eba.europa.eu. Run `uv run sync-sources && uv run
  extract-provisions` locally; the first real run should be on the 2020 file.
  A label rename or a missing column raises a `ValueError` that lists what the
  file actually contains.
- 2015–2017 files may predate the text `Label` column (numeric `Item` codes
  only, decoded by that year's data dictionary). The extractor refuses those
  with a clear message; extending it needs the per-year dictionary.
- IAS 39 → IFRS 9 on 1 Jan 2018: provisions jump on transition, so the Dec 2017
  (2018 ACS) and Dec 2018 (2019 ACS) figures sit either side of a regime break.
  Consider a post-IFRS 9 dummy before pooling.
- EBA definitions (value adjustments ÷ original exposure, UK counterparties)
  differ from the hand-compiled 2019 snapshot. Do not mix the two files in one
  fit; the app switches wholesale to the annual panel when it exists.
- Landing pages: 2015 <https://www.eba.europa.eu/risk-and-data-analysis/risk-analysis/2015-eu-wide-transparency-exercise>,
  2016 <https://www.eba.europa.eu/risk-and-data-analysis/risk-analysis/eu-wide-transparency-exercise/2016-eu-wide-transparency>,
  2017 <https://www.eba.europa.eu/risk-and-data-analysis/risk-analysis/2017-eu-wide-transparency-exercise>,
  2018 <https://www.eba.europa.eu/risk-and-data-analysis/risk-analysis/2018-eu-wide-transparency-exercise>,
  2019 <https://www.eba.europa.eu/risk-and-data-analysis/risk-analysis/eu-wide-transparency-exercise/2019-eu-wide-transparency>,
  2020 <https://www.eba.europa.eu/risk-and-data-analysis/risk-analysis/eu-wide-transparency-exercise/2020-eu-wide-transparency>.
  Each has a "Full database" link; the 2019 folder is
  `.../EU%20Wide%20Transparency%20Exercise/2019/Full%20database/` (its
  `TR_Metadata.xlsx` was seen there), the 2020 one adds a numeric subfolder.

### Fallback: firm annual reports / Pillar 3 (hand transcription)

Needed for the 2014, 2022 and 2025 tests, for Santander UK, and to cross-check
the EBA figures. Add rows to `firm_provisions_annual.csv` by hand; an extra
`source` column is allowed (the loader drops it). Tables to use:

| Firm | Table | Notes |
| --- | --- | --- |
| Barclays | Credit risk → "Loans and advances at amortised cost by product" (coverage ratio column); IFRS 9 era: "by stage" table | Group-level; ring-fenced Barclays Bank UK PLC reports separately from 2018 |
| HSBC | "Impairment allowances by industry sector" (Personal / Corporate & commercial); IFRS 9 era: "Allowance for ECL by stage" | Group segmentation is by industry/region; UK product split is in HSBC UK Bank plc accounts from 2018 |
| Lloyds | Asset quality → "Impaired loans and provisions by division"; IFRS 9 era: "ECL allowance and coverage by segment" (UK mortgages, credit cards) | Pillar 3 carries EU CR1-A |
| RBS / NatWest | "Risk elements in lending (REIL) and provisions by sector" ("provision coverage of REIL"); IFRS 9 era: "ECL allowance and coverage ratio by segment" | Some FY2014–2016 links below are results announcements, not the full ARA |
| Nationwide | Financial statements notes: residential mortgages and consumer banking impairment provisions | Fiscal year ends 4 April; use the April year-end nearest the start point |
| Santander UK | Credit risk → Retail Banking / Corporate & Commercial Banking loss allowance and NPL coverage | Entity changed to Santander UK Group Holdings plc from 2016 |
| Standard Chartered | "Loans and advances by client segment" with stage 3 cover ratio | Book is Asia/Africa/ME; excluded from modelling anyway |

Document URLs verified and used during transcription (corrections/additions to
the table below, downloaded directly):

- Barclays FY2018/FY2021 UK product split comes from the ring-fenced **Barclays
  Bank UK PLC** ARAs (the group AR URL served Barclays Bank PLC — wrong entity):
  [BBUK 2018](https://home.barclays/content/dam/home-barclays/documents/investor-relations/reports-and-events/annual-reports/2018/2018-barclays-bank-uk-plc-annual-report.pdf),
  [BBUK 2021](https://home.barclays/content/dam/home-barclays/documents/investor-relations/reports-and-events/annual-reports/2021/Barclays-Bank-UK-PLC-2021-Annual-Report.pdf).
- Barclays FY2017 IAS 39 group AR (full, not the transition note):
  <https://home.barclays/content/dam/home-barclays/documents/investor-relations/annualreports/ar2017/Barclays%20PLC%20Annual%20Report%202017.pdf>.
- HSBC UK product split comes from the UK subsidiaries (group ARA is regional):
  HSBC Bank plc 2015 (FY2015) and **HSBC UK Bank plc** 2018/2021 (FY2018/FY2021),
  all in GBP not USD.
- Santander UK FY2017 operating-company AR (the catalogued FY2017 entry is only
  an announcement page):
  <https://www.santander.co.uk/assets/s3fs-public/documents/santander_uk_plc_2017_annual_report_opco.pdf>.
- RBS/NatWest group figures: FY2021 from the NatWest Group ARA 2021; **FY2016
  (IAS 39) and FY2018 (IFRS 9) from the group's SEC EDGAR Form 20-F** (CIK
  844150), which reproduces the audited group credit-risk tables verbatim — the
  natwestgroup.com site exposes only subsidiary PDFs (RBS plc, RBS N.V.), the
  wrong-entity trap. 20-F URLs:
  [FY2016](https://www.sec.gov/Archives/edgar/data/844150/000095010317002773/dp74265_20f.htm),
  [FY2018](https://www.sec.gov/Archives/edgar/data/844150/000110465919011451/a18-40313_120f.htm).
  Still to source: RBS group FY2015 and FY2017 (2016 and 2018 ACS) — same 20-F route.

Document URLs seen verbatim in search results (unverified by direct download):

| Firm | FY2013 | FY2014 | FY2015 | FY2016 | FY2017 | FY2018 | FY2021 | FY2024 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Barclays | [AR](https://www.home.barclays/content/dam/home-barclays/documents/investor-relations/annualreports/ar2013/2013-barclays-annual-report-final.pdf) | [archive](https://home.barclays/investor-relations/reports-and-events/annual-reports/) | [AR](https://www.home.barclays/content/dam/home-barclays/documents/investor-relations/annualreports/ar2015/Barclays_PLC_Annual_Report_2015.pdf) | [AR](https://home.barclays/content/dam/home-barclays/documents/investor-relations/reports-and-events/annual-reports/Barclays-PLC-Annual-Report-2016-FINAL.pdf) | [IFRS 9 transition note](https://home.barclays/content/dam/home-barclays/documents/investor-relations/ResultAnnouncements/2017FYResults/20180308_IFRS9_Transition_Note.pdf) | [AR](https://home.barclays/content/dam/home-barclays/documents/investor-relations/reports-and-events/annual-reports/2018/barclays-plc-annual-report-2018.pdf) | [Pillar 3 Q1](https://home.barclays/content/dam/home-barclays/documents/investor-relations/ResultAnnouncements/Q12021/20210430-BarclaysPLC-Pillar3-Report.pdf) | [Pillar 3](https://home.barclays/content/dam/home-barclays/documents/investor-relations/ResultAnnouncements/FullYear2024Results/FY24-Barclays-PLC-Pillar-3-Report.pdf) |
| HSBC | [ARA](https://www.hsbc.com/-/files/hsbc/investors/investing-in-hsbc/all-reporting/group/2013/annual-results-2013/annual-reports-accounts-2013.pdf) | — | [HSBC Bank plc ARA](https://www.hsbc.com/-/files/hsbc/investors/investing-in-hsbc/all-reporting/subsidiaries/2015/annual-results/hsbc-bank-plc/hsbc-bank-plc-annual-report-and-accounts-2015.pdf) | [ARA](https://www.hsbc.com/-/files/hsbc/investors/investing-in-hsbc/all-reporting/group/2016/annual-results/hsbc-holdings-plc/170221-annual-report-and-accounts-2016.pdf) | [Pillar 3](https://www.hsbc.com/-/files/hsbc/investors/investing-in-hsbc/all-reporting/group/2017/annual-results/hsbc-holdings-plc/180220-pillar-3-disclosures-31-december-2017.pdf) | [ARA](https://www.hsbc.com/-/files/hsbc/investors/hsbc-results/2018/annual/hsbc-holdings-plc/190219-annual-report-and-accounts-2018.pdf) / [HSBC UK Bank plc](https://www.hsbc.com/-/files/hsbc/investors/hsbc-results/2018/annual/hsbc-uk-bank-plc/190219-annual-report-and-accounts-2018.pdf) | [HSBC UK Bank plc ARA](https://www.hsbc.com/-/files/hsbc/investors/hsbc-results/2021/annual/pdfs/hsbc-uk-bank-plc/220222-annual-report-and-accounts-2021.pdf) | [ARA](https://www.hsbc.com/-/files/hsbc/investors/hsbc-results/2024/annual/pdfs/hsbc-holdings-plc/250219-annual-report-and-accounts-2024.pdf) |
| Lloyds | [archive](https://www.lloydsbankinggroup.com/investors/annual-report/annual-report-archive.html) | — | [AR](https://www.lloydsbankinggroup.com/assets/pdfs/investors/annual-report/2015-download-links/2015_lbg_annual_report.pdf) | [AR](https://www.lloydsbankinggroup.com/assets/pdfs/investors/annual-report/2016-download-links/2016_lbg_annual_report.pdf) | [AR](https://www.lloydsbankinggroup.com/assets/pdfs/investors/annual-report/2017-download-links/2017_lbg_annual_report.pdf) | [AR](https://www.lloydsbankinggroup.com/assets/pdfs/investors/annual-report/2018-download-links/2018_lbg_annual_report.pdf) | [Pillar 3](https://www.lloydsbankinggroup.com/assets/pdfs/investors/financial-performance/lloyds-banking-group-plc/2021/q4/2021-lbg-fy-pillar3.pdf) | [archive](https://www.lloydsbankinggroup.com/investors/annual-report/annual-report-archive/annual-report-2024.html) |
| RBS / NatWest | [ARA](https://www.investors.rbs.com/~/media/Files/R/RBS-IR-V2/2013-reports/annual-report-and-accounts-2013.pdf) | [results](https://investors.natwestgroup.com/~/media/Files/R/RBS-IR-V2/annual-reports/rbs-ca.pdf) | [results](https://investors.natwestgroup.com/~/media/Files/R/RBS-IR-V2/annual-reports/rbs-plc-full-year-results-2015.pdf) | [results](https://investors.natwestgroup.com/~/media/Files/R/RBS-IR-V2/results-center/rbs-group-announcement-24-02-2017.pdf) | [ARA](https://investors.natwestgroup.com/~/media/Files/R/RBS-IR-V2/annual-report-2017/royal-bank%20of-scotland-annual-report-and-accounts%202017.pdf) | [ARA](https://www.investors.rbs.com/~/media/Files/R/RBS-IR-V2/results-center/15-02-2019/rbs-plc-ara-2018.pdf) | [ARA](https://investors.natwestgroup.com/~/media/Files/R/RBS-IR-V2/results-center/18022022/natwest-group-annual-report-accounts-2021.pdf) | [ARA](https://www.investors.rbs.com/~/media/Files/R/RBS-IR-V2/results-center/14022025/nwg-annual-report-and-accounts-2024.pdf) |
| Nationwide (FYE Apr of following year) | [ARA 2014](https://www.nationwide.co.uk/-/assets/nationwidecouk/documents/about/how-we-are-run/results-and-accounts/2013-2014/annual-results-and-accounts-2014.pdf) | [ARA 2015](https://www.nationwide.co.uk/-/assets/nationwidecouk/documents/about/how-we-are-run/results-and-accounts/2014-2015/annual-report-and-accounts-2015.pdf) | [ARA 2016](https://www.nationwide.co.uk/-/assets/nationwidecouk/documents/about/how-we-are-run/results-and-accounts/2015-2016/annual-report-and-accounts-2016.pdf) | — | [ARA 2018](https://www.nationwide.co.uk/-/assets/nationwidecouk/documents/about/how-we-are-run/results-and-accounts/2017-2018/annual-report-and-accounts-2018.pdf) | [ARA 2019](https://www.nationwide.co.uk/-/assets/nationwidecouk/documents/about/how-we-are-run/results-and-accounts/2018-2019/annual-report-and-accounts-2019.pdf) | [ARA 2022](https://www.nationwide.co.uk/-/assets/nationwidecouk/documents/about/how-we-are-run/results-and-accounts/2021-2022/annual-report-and-accounts-2022.pdf) | [ARA 2025](https://www.nationwide.co.uk/-/assets/nationwidecouk/documents/about/how-we-are-run/results-and-accounts/2024-2025/annual-report-and-accounts-2025.pdf) |
| Santander UK | [AR](https://www.santander.co.uk/assets/s3fs-public/documents/sanuk-2013-annual-report.pdf) | [AR](https://www.santander.co.uk/assets/s3fs-public/documents/2014_annual_report.pdf) | [AR](https://www.santander.co.uk/assets/s3fs-public/documents/santander_uk_plc_2015_annual_report_final.pdf) | [AR](https://assets.santandermedia.com/adobe/assets/urn:aaid:aem:0fcc03f2-b9cd-47d4-b8f8-9af17b06b32b/original/as/santander_uk_plc_2016_annual_report.pdf) | [announcement page](https://www.santander.co.uk/about-santander/investor-relations/stock-exchange-announcements/santander-uk-plc-2017-annual-report) | [AR](https://www.santander.co.uk/assets/s3fs-public/documents/2018_annual_report_santander_uk_plc-v2.pdf) | [Group Holdings AR](https://www.santander.co.uk/assets/s3fs-public/documents/santander_uk_group_holdings_plc_2021_annual_report_1.pdf) | [AR](https://www.santander.co.uk/assets/s3fs-public/documents/Santander%20UK%20plc%202024%20Annual%20Report.pdf) |
| Standard Chartered | [AR (mirror)](https://www.annualreports.com/HostedData/AnnualReportArchive/s/LSE_STAN_2013.pdf) | [AR](https://www.sc.com/EN/uploads/sites/66/content/docs/Annual_Report_2014.pdf) | — | — | [AR](https://www.sc.com/EN/uploads/sites/66/content/docs/Standard-Chartered-PLC-2017-Annual-Report.pdf) | [supplementary info](https://www.sc.com/en/uploads/sites/66/content/docs/supplementary-information-2018.pdf) | [financial statements](https://www.sc.com/en/uploads/sites/66/content/docs/annual-report-2021-financial-statements-and-notes.pdf) | [AR](https://www.sc.com/en/uploads/sites/66/content/docs/standard-chartered-plc-full-year-2024-report.pdf) |

### Derived table: `processed_inputs/firm_provisions_annual_reports.csv`

The mortgage and unsecured-retail coverage the EBA file cannot supply (IRB
banks report retail in one aggregate class), transcribed by hand from the
firm annual reports / Pillar 3 disclosures above and committed as a
long-format panel — one row per firm × ACS year × product. It complements
the EBA-sourced commercial column; merging the two into a single annual
panel (annual-report mortgage/retail + EBA commercial) and wiring it into
the model is a planned follow-up, not yet done.

**Columns.** `firm_name, acsyear, product ("mortgage"|"unsecured_retail"),
allowance, gross_loans, coverage, basis ("IAS39"|"IFRS9"), entity, currency,
source_url, source_table, source_page, notes`. Provenance attaches to every
number (table title + page), and both the numerator (`allowance`, the
balance-sheet impairment stock) and denominator (`gross_loans`) are kept so
`coverage = allowance / gross_loans` can be re-derived.

**Definitions.**

- **Coverage** = impairment allowance (balance-sheet stock, *not* the P&L
  charge) ÷ gross loans, per product, at the test start point (31 December of
  the year before the ACS; Nationwide uses its nearest 4 April year-end).
- **mortgage** = UK residential mortgages. **unsecured_retail** = credit cards
  + personal loans + overdrafts (excludes auto/motor and secured lending).
- **basis**: IAS 39 (incurred loss) for FY2017 and earlier; IFRS 9 (ECL) from
  FY2018. Not comparable across the 1 Jan 2018 transition — each step flagged.
- **entity**: group level, except where only a ring-fenced UK sub (HSBC UK
  Bank plc, Barclays Bank UK PLC, both from 2018) gives the UK product split.
- A firm-year that reports only a blended retail line (no mortgage/unsecured
  split) is left blank with an explaining note — not guessed.

**Tooling.** `uv run validate-annual-reports`
(`src/uk_stress_benchmark/annual_reports.py`) loads the file, checks the
required columns, product/basis vocabularies and numerator/denominator
completeness, recomputes `coverage` and refuses any hand-entered ratio that
contradicts its two figures, and flags any coverage outside its product's
plausible band (mortgage ~0.05–0.6%, unsecured ~3–12%). Raw figures are
mirrored, with source/unit/period/definition, in
[appendix-detailed-data.md](appendix-detailed-data.md).

**Progress.** Being filled one firm-year at a time (resumable). Populated
(ACS years): Lloyds 2016–2019, Nationwide 2016–2019 + 2022, Santander UK
2016–2019 + 2022, Barclays 2019 + 2022 (ring-fenced Barclays Bank UK PLC),
HSBC 2016 (HSBC Bank plc) + 2019 + 2022 (HSBC UK Bank plc), RBS/NatWest 2017 +
2019 + 2022 (group, via Form 20-F). Documented gaps: Barclays and HSBC IAS 39 years (2017/2018
ACS) disclose UK gross by product but the impairment allowance only group-wide
by asset class or by region, so a UK product-coverage ratio can't be computed.
Standard Chartered is excluded (no UK retail book; excluded from modelling).
Still open: RBS/NatWest group figures for 2016 and 2018 ACS (FY2015/FY2017,
same 20-F route), and the Phase-2 years (2014, 2015, 2025).

### Checked and not usable

- BoE stress-test results annexes: bank-specific *impairment charge* rates only
  (already ingested); no starting-point coverage table was found (not confirmed
  by direct read).
- BoE Bankstats, EBA Risk Dashboard, UK Finance statistics: aggregate only, no
  per-firm series; the EBA dashboard also drops UK banks from 2021.

## TBD — origin not confirmed

These appeared in the legacy folder; original source is not recorded. Pete to fill in:

- `eco_scenarios_low_point.csv` — possibly a derived intermediate, not a raw source.
- `results.csv` / `results.numbers` — firm-level impairment-charge percentages keyed by ACS year. Likely manually compiled from the BoE results PDFs above; confirm.
