# Data sources

Raw source files for `raw_inputs/` are kept locally only (gitignored). This file records where each one came from so the workspace can be reconstructed on a fresh machine. Update it whenever a raw file is added or replaced.

URLs are not committed unless verified — most public regulatory data lives behind landing pages that move year-to-year. For each entry, search the publisher's site by the title or filename rather than relying on a URL.

## Bank of England — concurrent stress-test scenarios

Published annually alongside the BoE concurrent stress-test exercise. Source: bankofengland.co.uk, "Stress testing" section.

| Filename | Year | Notes |
| --- | --- | --- |
| `stress-testing-the-uk-banking-system-variable-paths-for-the-2014-scenario.xlsx` | 2014 | ACS scenario macro variable paths |
| `stress-testing-the-uk-banking-system-variable-paths-for-the-2015-scenario.xlsx` | 2015 | |
| `variable-paths-for-the-2016-stress-test.xlsx` | 2016 | |
| `stress-testing-the-uk-banking-system-variable-paths-for-the-2017-scenario.xlsx` | 2017 | |
| `stress-testing-the-uk-banking-system-variable-paths-for-the-2018-scenario.xlsx` | 2018 | |
| `stress-testing-the-uk-banking-system-variable-paths-for-the-2019-scenario.xlsx` | 2019 | |
| `variable-paths-for-firms-not-participating-in-2019-concurrent-stress-test.XLSX` | 2019 | Non-participating firms |
| `stress-testing-the-uk-banking-system-2014-results.pdf` … `-2017-results.pdf` | 2014–2017 | Annual results commentaries |
| `november-2018.pdf` | 2018 | BoE Financial Stability Report (containing 2018 stress-test results) |
| `december-2019.pdf` | 2019 | BoE FSR with 2019 stress-test results |
| `mlar-longrun-detailed.xlsx` | — | Long-run Mortgage Lenders & Administrators Return data |
| `effectiveness-of-stresstesting-model-risk-management.pdf` | — | BoE working/staff paper |
| `mortgages-estimating-default-correlation-and-forecasting-default-risk.pdf` | — | BoE working/staff paper |

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
| `HSBC 2018 CREL ltv profile UK.xlsx` | HSBC | 2018 UK CRE LTV profile |
| `standard-chartered-plc-full-year-2019-data-pack.xlsx` | Standard Chartered | FY 2019 data pack |

## TBD — origin not confirmed

These appeared in the legacy folder; original source is not recorded. Pete to fill in:

- `eco_scenarios_low_point.csv` — possibly a derived intermediate, not a raw source.
- `results.csv` / `results.numbers` — firm-level impairment-charge percentages keyed by ACS year. Likely manually compiled from the BoE results PDFs above; confirm.
