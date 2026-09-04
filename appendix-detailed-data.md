# Appendix — detailed data provenance

Raw figures behind the processed datasets, captured with source, unit, period
and definition so every derived number can be re-checked against the primary
document. This appendix is committed; the source PDFs live in `raw_inputs/`
(gitignored, reproducible from the URLs in [SOURCES.md](SOURCES.md) and in the
`source_url` column of each CSV).

---

## Mortgage & unsecured-retail provision coverage (annual reports)

Feeds `processed_inputs/firm_provisions_annual_reports.csv`. **Coverage =
impairment allowance (balance-sheet stock) / gross loans, per product**, at the
test's start point (31 December of the year before the ACS; Nationwide uses its
nearest 4 April year-end). Numerator (`allowance`) and denominator
(`gross_loans`) are captured separately so the ratio is re-derivable; coverage
is computed in code, never hand-typed.

Definitions applied consistently:

- **mortgage** — UK residential mortgages.
- **unsecured_retail** — credit cards + personal loans + overdrafts (excludes
  auto/motor and any secured lending). Commercial is out of scope here (sourced
  from the EBA file; see SOURCES.md).
- **basis** — IAS 39 (incurred loss) for FY2017 and earlier; IFRS 9 (expected
  credit loss) from FY2018. The two are **not comparable across the 1 Jan 2018
  transition**: IFRS 9 ECL allowances are structurally larger than IAS 39
  incurred-loss provisions, most visibly on unsecured books (e.g. Lloyds
  unsecured roughly doubles, 1.8% -> 3.5%, across the break).
- **entity** — group level to match the rest of the dataset, except where only
  a ring-fenced UK sub discloses the UK product split (Barclays Bank UK PLC from
  2018; HSBC UK Bank plc from 2018), recorded in the `entity` column.
- A firm-year with no usable mortgage/unsecured split is left blank with an
  explaining note (a documented gap), never guessed.

All amounts are £m unless the currency column says otherwise. `acsyear` is the
stress-test year; the balance-sheet date is 31 December of the prior year
(Nationwide: the stated 4 April year-end).


### Barclays

| ACS | Basis | Entity | Product | Allowance | Gross | Coverage | Source table | Page |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | IAS39 | Barclays PLC (group segment) | mortgage | — | — | gap | Home loans principal portfolios (gross only) | FY2013 AR, PDF p165; group allowance PDF p154 |
| 2014 | IAS39 | Barclays PLC (group segment) | unsecured_retail | — | — | gap | Credit cards/unsecured principal portfolios (gross only) | FY2013 AR, PDF p169; group allowance PDF p154 |
| 2015 | IAS39 | Barclays PLC (group segment) | mortgage | — | — | gap | Home loans principal portfolios (gross only) | FY2014 AR, PDF p157; group allowance PDF p173 |
| 2015 | IAS39 | Barclays PLC (group segment) | unsecured_retail | — | — | gap | Credit cards/unsecured principal portfolios (gross only) | FY2014 AR, PDF p160; group allowance PDF p173 |
| 2016 | IAS39 | Barclays PLC (group segment) | mortgage | — | — | gap | Home loans principal portfolios (gross only) | FY2015 AR, PDF p155; group allowance PDF p170 |
| 2016 | IAS39 | Barclays PLC (group segment) | unsecured_retail | — | — | gap | Credit cards/unsecured principal portfolios (gross only) | FY2015 AR, PDF p158; group allowance PDF p170 |
| 2017 | IAS39 | Barclays PLC (group segment) | mortgage | — | — | gap | Home loans / Credit cards principal portfolios (gross only) | FY2016 AR, PDF p176-p186 |
| 2017 | IAS39 | Barclays PLC (group segment) | unsecured_retail | — | — | gap | Credit cards / unsecured loans principal portfolios (gross only) | FY2016 AR, PDF p177-p186 |
| 2018 | IAS39 | Barclays PLC (group segment) | mortgage | — | — | gap | Home loans / Credit cards principal portfolios (gross only) | FY2017 AR, PDF p148-p156 |
| 2018 | IAS39 | Barclays PLC (group segment) | unsecured_retail | — | — | gap | Credit cards / unsecured loans principal portfolios (gross only) | FY2017 AR, PDF p149-p156 |
| 2019 | IFRS9 | Barclays Bank UK PLC | mortgage | 84 | 137,208 | 0.0612% | Loans and advances at amortised cost by product - Barclays Bank UK Group (audited): Home loans | printed p53 (PDF p55), 2018 Barclays Bank UK PLC AR |
| 2019 | IFRS9 | Barclays Bank UK PLC | unsecured_retail | 2,582 | 25,208 | 10.2428% | Loans and advances at amortised cost by product - Barclays Bank UK Group (audited): Credit cards, unsecured loans and other retail lending | printed p53 (PDF p55), 2018 Barclays Bank UK PLC AR |
| 2022 | IFRS9 | Barclays Bank UK PLC | mortgage | 89 | 158,309 | 0.0562% | Loans and advances at amortised cost by product - Barclays Bank UK Group (audited): Home loans | printed p66 (PDF p67), 2021 Barclays Bank UK PLC AR |
| 2022 | IFRS9 | Barclays Bank UK PLC | unsecured_retail | 1,664 | 15,089 | 11.0279% | Loans and advances at amortised cost by product - Barclays Bank UK Group (audited): Credit cards, unsecured loans and other retail lending | printed p66 (PDF p67), 2021 Barclays Bank UK PLC AR |
| 2025 | IFRS9 | Barclays Bank UK PLC | mortgage | 146 | 163,251 | 0.0894% | Loans and advances at amortised cost by product - Barclays Bank UK Group (audited): Retail mortgages | printed p83 (PDF p84), 2024 Barclays Bank UK PLC AR |
| 2025 | IFRS9 | Barclays Bank UK PLC | unsecured_retail | 1,082 | 24,443 | 4.4266% | Loans and advances at amortised cost by product - Barclays Bank UK Group (audited): Retail credit cards + Retail other | printed p83 (PDF p84), 2024 Barclays Bank UK PLC AR |

Notes:

- **2014 mortgage** — GAP: IAS 39 discloses UK gross by product but the impairment allowance only group-wide by asset class (spans US/Iberia/SA cards, non-UK home loans, etc.), never UK x product. UK product coverage not computable. UK home loans gross 122,880m; group-wide home-loans allowance 788m.
- **2014 unsecured_retail** — GAP: IAS 39 discloses UK gross by product but the impairment allowance only group-wide by asset class (spans US/Iberia/SA cards, non-UK home loans, etc.), never UK x product. UK product coverage not computable. UK cards 15,937 + personal loans 4,958 + overdrafts 1,307; group cards/unsecured allowance 3,603m.
- **2015 mortgage** — GAP: IAS 39 discloses UK gross by product but the impairment allowance only group-wide by asset class (spans US/Iberia/SA cards, non-UK home loans, etc.), never UK x product. UK product coverage not computable. PCB-UK home loans gross 126,668m; group-wide home-loans allowance 547m.
- **2015 unsecured_retail** — GAP: IAS 39 discloses UK gross by product but the impairment allowance only group-wide by asset class (spans US/Iberia/SA cards, non-UK home loans, etc.), never UK x product. UK product coverage not computable. UK cards 17,447 + personal loans 4,953 + overdrafts 902; group cards/unsecured allowance 3,345m.
- **2016 mortgage** — GAP: IAS 39 discloses UK gross by product but the impairment allowance only group-wide by asset class (spans US/Iberia/SA cards, non-UK home loans, etc.), never UK x product. UK product coverage not computable. PCB-UK home loans gross 127,750m; group-wide home-loans allowance 518m.
- **2016 unsecured_retail** — GAP: IAS 39 discloses UK gross by product but the impairment allowance only group-wide by asset class (spans US/Iberia/SA cards, non-UK home loans, etc.), never UK x product. UK product coverage not computable. UK cards 18,502 + personal loans 5,476 (no separate UK-overdrafts line in FY2015); group allowance 3,394m.
- **2017 mortgage** — GAP: IAS 39 discloses UK gross by product (Barclays UK home loans 129,136m; UK cards 17,833 + UK personal loans 6,076) but impairment allowance only group-wide by asset class (home loans 467m incl. non-UK), never UK x product. UK coverage not computable.
- **2017 unsecured_retail** — GAP: UK unsecured gross partly available (cards+personal loans) but allowance only group-wide by asset class (cards/unsecured 3,060m incl. US cards, Partner Finance motor). Not computable.
- **2018 mortgage** — GAP: as FY2016 — UK gross by product available (home loans 132,132m) but allowance only group-wide by asset class (home loans 458m incl. non-UK). UK coverage not computable.
- **2018 unsecured_retail** — GAP: as FY2016 — allowance only group-wide by asset class (cards/unsecured 3,055m). UK unsecured coverage not computable.
- **2019 mortgage** — Home loans = UK residential mortgages. Ring-fenced Barclays Bank UK PLC (the catalogued group AR URL served Barclays Bank PLC, whose home loans are only 13.5bn - wrong entity). IFRS 9 ECL, all stages (Total column).
- **2019 unsecured_retail** — 'Credit cards, unsecured loans and other retail lending' = UK cards + personal loans + overdrafts + other unsecured; no motor/auto in the ring-fenced bank. IFRS 9 ECL, all stages.
- **2022 mortgage** — Home loans = UK residential mortgages. Ring-fenced Barclays Bank UK PLC (catalogued FY2021 link was a Q1-2021 Pillar 3 - wrong period). IFRS 9 ECL, all stages.
- **2022 unsecured_retail** — Unsecured = cards + personal loans + overdrafts + other; no motor. IFRS 9 ECL, all stages.
- **2025 mortgage** — Retail mortgages = UK residential mortgages, ring-fenced Barclays Bank UK PLC. IFRS 9 ECL, all stages (Total).
- **2025 unsecured_retail** — Unsecured = Retail credit cards (750/15,780) + Retail other (332/8,663) = 1,082/24,443; no motor in the ring-fenced bank. IFRS 9 ECL, all stages.

### HSBC

| ACS | Basis | Entity | Product | Allowance | Gross | Coverage | Source table | Page |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | IAS39 | HSBC Bank plc (UK) | mortgage | 222 | 79,955 | 0.2777% | Mortgage lending by product type (UK column) | printed p36 (PDF p38), 2013 HSBC Bank plc ARA |
| 2014 | IAS39 | HSBC Bank plc (UK) | unsecured_retail | 274 | 13,860 | 1.9769% | Total personal lending (UK column), 31 Dec 2013 comparative | printed p56 (PDF p58), 2014 HSBC Bank plc ARA |
| 2015 | IAS39 | HSBC Bank plc (UK) | mortgage | 155 | 79,066 | 0.1960% | Total personal lending (UK column): Residential mortgage lending | printed p56 (PDF p58), 2014 HSBC Bank plc ARA |
| 2015 | IAS39 | HSBC Bank plc (UK) | unsecured_retail | 209 | 13,489 | 1.5494% | Total personal lending (UK column): Other personal lending | printed p56 (PDF p58), 2014 HSBC Bank plc ARA |
| 2016 | IAS39 | HSBC Bank plc (UK) | mortgage | 117 | 79,173 | 0.1478% | Total personal lending (UK column): Residential mortgage lending | printed p42 (PDF p44), 2015 HSBC Bank plc ARA |
| 2016 | IAS39 | HSBC Bank plc (UK) | unsecured_retail | 199 | 14,032 | 1.4182% | Total personal lending (UK column): Other personal lending | printed p42 (PDF p44), 2015 HSBC Bank plc ARA |
| 2017 | IAS39 | HSBC Holdings group | mortgage | — | — | gap | Total personal lending (regional, not UK) | 2016 group ARA |
| 2017 | IAS39 | HSBC Holdings group | unsecured_retail | — | — | gap | Total personal lending (regional, not UK) | 2016 group ARA |
| 2018 | IAS39 | HSBC Holdings group (Pillar 3) | mortgage | — | — | gap | Pillar 3 (regulatory exposure classes, no UK product loans/allowance table) | 2017 Pillar 3 |
| 2018 | IAS39 | HSBC Holdings group (Pillar 3) | unsecured_retail | — | — | gap | Pillar 3 (regulatory exposure classes) | 2017 Pillar 3 |
| 2019 | IFRS9 | HSBC UK Bank plc | mortgage | 107 | 94,703 | 0.1130% | Total personal lending by stage distribution: First lien residential mortgages | printed p40 (PDF p42), 2018 HSBC UK Bank plc ARA |
| 2019 | IFRS9 | HSBC UK Bank plc | unsecured_retail | 458 | 15,505 | 2.9539% | Total personal lending by stage distribution: Other personal lending | printed p40 (PDF p42), 2018 HSBC UK Bank plc ARA |
| 2022 | IFRS9 | HSBC UK Bank plc | mortgage | 163 | 118,077 | 0.1380% | Total personal lending by stage distribution: First lien residential mortgages | printed p47 (PDF p49), 2021 HSBC UK Bank plc ARA |
| 2022 | IFRS9 | HSBC UK Bank plc | unsecured_retail | 604 | 13,241 | 4.5616% | Total personal lending by stage distribution: Other personal lending | printed p47 (PDF p49), 2021 HSBC UK Bank plc ARA |
| 2025 | IFRS9 | HSBC UK Bank plc | mortgage | 105 | 132,894 | 0.0790% | Total personal lending by stage distribution: First lien residential mortgages | printed p53 (PDF p55), 2024 HSBC UK Bank plc ARA |
| 2025 | IFRS9 | HSBC UK Bank plc | unsecured_retail | 426 | 14,372 | 2.9641% | Total personal lending by stage distribution: Other personal lending | printed p53 (PDF p55), 2024 HSBC UK Bank plc ARA |

Notes:

- **2014 mortgage** — UK residential mortgages, UK column. HSBC Bank plc reports in GBP. IAS 39 allowance stock. Cross-validated against the 2014 ARA's 31 Dec 2013 comparative (79,955/222).
- **2014 unsecured_retail** — Other personal lending (UK) = personal loans & overdrafts (194/6,916) + credit cards (80/6,944) = 274/13,860; motor nil in UK column. 31 Dec 2013 figures taken from the 2014 ARA comparative (the 2013 ARA gives other-personal at group level only). IAS 39.
- **2015 mortgage** — UK residential mortgages, UK column. IAS 39 allowance stock.
- **2015 unsecured_retail** — Other personal lending (UK) = personal loans & overdrafts (145/6,655) + credit cards (64/6,834) = 209/13,489; motor nil in UK column. IAS 39.
- **2016 mortgage** — UK residential mortgages, UK column. HSBC Bank plc reports in GBP. IAS 39 allowance stock.
- **2016 unsecured_retail** — Other personal lending (UK) = personal loans & overdrafts (7,073/147) + credit cards (6,959/52); motor is nil in the UK column, so nothing to exclude. IAS 39.
- **2017 mortgage** — GAP: group ARA splits personal lending by region (Europe/Asia/...), not UK; 'Europe' is broader than the UK. UK split would need the HSBC Bank plc 2016 subsidiary ARA (not catalogued; mirror URL 404s).
- **2017 unsecured_retail** — GAP: regional split only (Europe != UK). See HSBC 2017 mortgage note.
- **2018 mortgage** — GAP: FY2017 Pillar 3 is Basel EAD/RWA by exposure class, no IAS 39 UK-product gross+allowance. UK split would need the HSBC Bank plc 2017 subsidiary ARA (not catalogued).
- **2018 unsecured_retail** — GAP: see HSBC 2018 mortgage note.
- **2019 mortgage** — First lien UK residential mortgages, ring-fenced HSBC UK Bank plc (first exists FY2018). IFRS 9 ECL, all stages. Entity scope differs from FY2015 HSBC Bank plc (UK column).
- **2019 unsecured_retail** — Other personal lending = 'other' (personal loans & overdrafts 8,226/218) + credit cards (7,279/240); no motor line in the UK ring-fenced bank. IFRS 9 ECL, all stages.
- **2022 mortgage** — First lien UK residential mortgages. IFRS 9 ECL, all stages.
- **2022 unsecured_retail** — Other personal lending = 'other' (7,222/285) + credit cards (6,019/319); no motor. IFRS 9 ECL.
- **2025 mortgage** — First lien UK residential mortgages, ring-fenced HSBC UK Bank plc. IFRS 9 ECL, all stages.
- **2025 unsecured_retail** — Other personal lending = 'other' (personal loans & overdrafts 201/8,048) + credit cards (225/6,324) = 426/14,372; no motor line. IFRS 9 ECL, all stages.

### Lloyds Banking Group

| ACS | Basis | Entity | Product | Allowance | Gross | Coverage | Source table | Page |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | IAS39 | Lloyds Banking Group | mortgage | 1,472 | 323,107 | 0.4556% | Table 1.11 Impairments on Retail loans and advances (Secured) | printed p145 (PDF p147), 2013 ARA |
| 2014 | IAS39 | Lloyds Banking Group | unsecured_retail | 578 | 21,566 | 2.6801% | Table 1.11 (Retail unsecured provisions) + Table 1.12 (unsecured gross components) | printed p145-147 (PDF p147-149), 2013 ARA |
| 2015 | IAS39 | Lloyds Banking Group | mortgage | 1,446 | 303,121 | 0.4770% | Table 1.10 Retail impaired loans and provisions (Secured), 2014 comparative | printed p130 (PDF p132), 2015 ARA |
| 2015 | IAS39 | Lloyds Banking Group | unsecured_retail | 386 | 19,514 | 1.9781% | Table 1.10 (Retail Loans & overdrafts 220/10,395) + Table 1.26 (Consumer Finance Credit Cards 166/9,119), 2014 comparative | printed p130 & p137 (PDF p132 & p139), 2015 ARA |
| 2016 | IAS39 | Lloyds Banking Group | mortgage | 1,431 | 302,413 | 0.4732% | Table 1.10 Retail impaired loans and provisions (Secured) | PDF p132 (2015 ARA) |
| 2016 | IAS39 | Lloyds Banking Group | unsecured_retail | 350 | 19,342 | 1.8095% | Table 1.10 (Loans & overdrafts 197/9,917) + Table 1.26 Consumer Finance (Credit Cards 153/9,425) | PDF p132 & p139 (2015 ARA) |
| 2017 | IAS39 | Lloyds Banking Group | mortgage | 1,503 | 294,503 | 0.5104% | Table 1.9 Retail impaired loans and provisions (Secured) | PDF p136 (2016 ARA) |
| 2017 | IAS39 | Lloyds Banking Group | unsecured_retail | 339 | 19,562 | 1.7330% | Table 1.9 (Overdrafts 90/1,952) + Table 1.24 Consumer Finance (Credit cards 157/9,843, Loans 92/7,767) | PDF p136 & p144 (2016 ARA) |
| 2018 | IAS39 | Lloyds Banking Group | mortgage | 1,443 | 292,187 | 0.4939% | Table 1.9: Retail impaired loans and provisions | p123 (PDF p125) |
| 2018 | IAS39 | Lloyds Banking Group | unsecured_retail | 487 | 27,739 | 1.7557% | Table 1.9: Retail impaired loans and provisions | p123 (PDF p125) |
| 2019 | IFRS9 | Lloyds Banking Group | mortgage | 460 | 288,235 | 0.1596% | Statutory basis: Table 1.10 (gross) & Table 1.11 (ECL allowance drawn+undrawn) | PDF p126 (gross) & p128 (allowance), 2018 ARA |
| 2019 | IFRS9 | Lloyds Banking Group | unsecured_retail | 896 | 28,115 | 3.1869% | Statutory basis: Table 1.10 (gross) & Table 1.11 (ECL allowance drawn+undrawn) | PDF p126 (gross) & p128 (allowance), 2018 ARA |
| 2022 | IFRS9 | Lloyds Banking Group | mortgage | 837 | 308,344 | 0.2715% | Loans and advances to customers and ECL allowance (statutory basis): UK mortgages | printed p156 (PDF p158), 2021 ARA |
| 2022 | IFRS9 | Lloyds Banking Group | unsecured_retail | 966 | 24,074 | 4.0126% | Loans and advances to customers and ECL allowance (statutory basis): Credit cards + Loans and overdrafts | printed p156 (PDF p158), 2021 ARA |
| 2025 | IFRS9 | Lloyds Banking Group | mortgage | 852 | 313,128 | 0.2721% | Loans and advances to customers and ECL allowance (statutory basis): UK mortgages | printed p164 (PDF p168), 2024 ARA |
| 2025 | IFRS9 | Lloyds Banking Group | unsecured_retail | 1,197 | 26,976 | 4.4373% | Loans and advances to customers and ECL allowance (statutory basis): Credit cards + UK unsecured loans and overdrafts | printed p164 (PDF p168), 2024 ARA |

Notes:

- **2014 mortgage** — Secured = UK residential mortgages. IAS 39 impairment provisions / gross.
- **2014 unsecured_retail** — Unsecured = whole Retail 'unsecured' line = Credit cards (9,373) + Personal loans (9,595) + Overdrafts (2,598) = 21,566 gross; 578 provisions. No Consumer Finance division in 2013; Motor/Asset Finance sat in a separate division, excluded. IAS 39.
- **2015 mortgage** — Secured = UK residential mortgages. FY2014 from the 2015 ARA comparative. IAS 39.
- **2015 unsecured_retail** — Unsecured = Credit Cards (Consumer Finance) + Retail 'Loans and overdrafts' = 386/19,514. The 2014 Consumer Finance table has no separate 'Loans' line (personal loans + overdrafts sit in the Retail combined line); Asset Finance UK (Motor) and Europe excluded. IAS 39.
- **2016 mortgage** — Secured = UK residential mortgages. IAS 39 total impairment provisions / gross.
- **2016 unsecured_retail** — Unsecured = Credit cards + personal loans + overdrafts (allowance 350m, gross 19,342m). Excludes Asset/Motor Finance (UK+Europe), Wealth, Retail Business Banking. IAS 39.
- **2017 mortgage** — Secured = UK residential mortgages. IAS 39 total impairment provisions / gross.
- **2017 unsecured_retail** — Unsecured = Credit cards + Loans + Overdrafts (allowance 339m, gross 19,562m). Excludes UK Motor Finance, Europe, Wealth, Retail Business Banking. IAS 39.
- **2018 mortgage** — Secured = UK residential mortgages. IAS 39 total impairment provisions (incl. collective unidentified) / gross loans and advances. Lloyds' own printed metric is provisions/impaired-loans = 37.1%.
- **2018 unsecured_retail** — Unsecured = Credit cards (267/18,134) + Loans (107/8,010) + Overdrafts (113/1,595); allowance 487m, gross 27,739m. Excludes UK Motor Finance, Retail Business Banking, Europe. IAS 39 incurred-loss basis (runs below the IFRS 9 unsecured band by design).
- **2019 mortgage** — Secured = UK residential mortgages. STATUTORY basis (actual IFRS 9 balance sheet, net of HBOS/MBNA pre-acquisition ECL) for cross-firm comparability; reproduces Lloyds' printed 0.2%. Underlying-basis figure was 1,462/289,237 = 0.505%.
- **2019 unsecured_retail** — Unsecured = Credit cards, Loans and Overdrafts (footnote 2); UK Motor Finance excluded. STATUTORY basis; reproduces printed 3.2%. Underlying-basis figure was 980/27,990 = 3.50%.
- **2022 mortgage** — UK mortgages. STATUTORY basis (statutory Total gross incl. POCI; Customer-related ECL allowance drawn+undrawn), consistent with how FY2018 was recorded. Unsecured = Credit cards + Loans/overdrafts; UK Motor Finance and Other excluded.
- **2022 unsecured_retail** — Unsecured = Credit cards (521/14,517) + Loans and overdrafts (445/9,557) = 966/24,074. STATUTORY basis (statutory Total gross incl. POCI; Customer-related ECL allowance drawn+undrawn), consistent with how FY2018 was recorded. Unsecured = Credit cards + Loans/overdrafts; UK Motor Finance and Other excluded.
- **2025 mortgage** — UK mortgages. STATUTORY basis (statutory Total gross incl. POCI; Customer-related ECL allowance drawn+undrawn), consistent with how FY2018 was recorded. Unsecured = Credit cards + Loans/overdrafts; UK Motor Finance and Other excluded.
- **2025 unsecured_retail** — Unsecured = Credit cards (674/16,240) + UK unsecured loans and overdrafts (523/10,736) = 1,197/26,976. ('Loans and overdrafts' renamed 'UK unsecured loans and overdrafts' in 2024.) STATUTORY basis (statutory Total gross incl. POCI; Customer-related ECL allowance drawn+undrawn), consistent with how FY2018 was recorded. Unsecured = Credit cards + Loans/overdrafts; UK Motor Finance and Other excluded.

### Nationwide

| ACS | Basis | Entity | Product | Allowance | Gross | Coverage | Source table | Page |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | IAS39 | Nationwide Building Society | mortgage | 102 | 145,660 | 0.0700% | Loans and advances to customers + residential-mortgage impairment (Prime + Specialist) | PDF p89-90, FYE 4 Apr 2014 |
| 2014 | IAS39 | Nationwide Building Society | unsecured_retail | 173 | 3,862 | 4.4795% | Consumer banking impairment provisions | printed p104 (PDF p106), FYE 4 Apr 2014 |
| 2015 | IAS39 | Nationwide Building Society | mortgage | 110 | 152,885 | 0.0719% | Maximum exposure to lending risk - Loans and advances to customers | printed p102 (PDF p102), FYE 4 Apr 2015 |
| 2015 | IAS39 | Nationwide Building Society | unsecured_retail | 216 | 3,791 | 5.6977% | Maximum exposure to lending risk - Loans and advances to customers | printed p102 (PDF p102), FYE 4 Apr 2015 |
| 2016 | IAS39 | Nationwide Building Society | mortgage | 102 | 162,164 | 0.0629% | Maximum exposure to lending risk (Business and Risk Report) | p112 (PDF p113), FYE 4 Apr 2016 |
| 2016 | IAS39 | Nationwide Building Society | unsecured_retail | 281 | 3,869 | 7.2629% | Maximum exposure to lending risk (Business and Risk Report) | p112 (PDF p113), FYE 4 Apr 2016 |
| 2017 | IAS39 | Nationwide Building Society | mortgage | 144 | 171,263 | 0.0841% | Maximum exposure to credit risk — 2017 comparative column (Business and Risk Report) | p106 (PDF p107), FYE 4 Apr 2017 comparative in the 2018 ARA |
| 2017 | IAS39 | Nationwide Building Society | unsecured_retail | 269 | 3,949 | 6.8119% | Maximum exposure to credit risk — 2017 comparative column (Business and Risk Report) | p106 (PDF p107), FYE 4 Apr 2017 comparative in the 2018 ARA |
| 2018 | IAS39 | Nationwide Building Society | mortgage | 145 | 177,299 | 0.0818% | Maximum exposure to credit risk (Business and Risk Report) | p106 (PDF p107), FYE 4 Apr 2018 |
| 2018 | IAS39 | Nationwide Building Society | unsecured_retail | 298 | 4,107 | 7.2559% | Maximum exposure to credit risk (Business and Risk Report) | p106 (PDF p107), FYE 4 Apr 2018 |
| 2019 | IFRS9 | Nationwide Building Society | mortgage | 206 | 185,940 | 0.1108% | Maximum exposure to credit risk — amortised cost (Business and Risk Report) | p108 (PDF p109), FYE 4 Apr 2019 |
| 2019 | IFRS9 | Nationwide Building Society | unsecured_retail | 418 | 4,586 | 9.1147% | Maximum exposure to credit risk — amortised cost (Business and Risk Report) | p108 (PDF p109), FYE 4 Apr 2019 |
| 2022 | IFRS9 | Nationwide Building Society | mortgage | 187 | 198,056 | 0.0944% | Maximum exposure to credit risk — amortised cost (Business and Risk Report) | p142 (PDF p143), FYE 4 Apr 2022 |
| 2022 | IFRS9 | Nationwide Building Society | unsecured_retail | 529 | 4,638 | 11.4058% | Maximum exposure to credit risk — amortised cost (Business and Risk Report) | p142 (PDF p143), FYE 4 Apr 2022 |
| 2025 | IFRS9 | Nationwide Building Society | mortgage | 351 | 275,890 | 0.1272% | Maximum exposure to credit risk - Group (amortised cost) | printed p131 (PDF p131), FYE 31 Mar 2025 |
| 2025 | IFRS9 | Nationwide Building Society | unsecured_retail | 824 | 11,107 | 7.4187% | Maximum exposure to credit risk - Group (amortised cost): Consumer lending | printed p131 (PDF p131), FYE 31 Mar 2025 |

Notes:

- **2014 mortgage** — Residential mortgages. Allowance 102 = Prime 18 + Specialist 84 (the 2014 report gives no single combined line; the combined 102 is printed in the 2015 report's 4 Apr 2014 comparative). Consumer banking = unsecured; no motor. IAS 39.
- **2014 unsecured_retail** — Consumer banking = unsecured (current-account overdrafts, personal loans, credit cards); no motor. Allowance 173, gross 3,862. IAS 39.
- **2015 mortgage** — Residential mortgages. Same table format as 2016-2022. Consumer banking = unsecured; no motor. IAS 39.
- **2015 unsecured_retail** — Consumer banking = unsecured; no motor. Allowance 216, gross 3,791. IAS 39.
- **2016 mortgage** — Residential mortgages. Consumer banking = unsecured lending (current-account overdrafts, personal loans, credit cards); Nationwide has no motor book. Allowance = balance-sheet impairment provision stock. Year-end 4 April (nearest to the ACS start point).
- **2016 unsecured_retail** — Consumer banking = unsecured lending (current-account overdrafts, personal loans, credit cards); Nationwide has no motor book. Allowance = balance-sheet impairment provision stock. Year-end 4 April (nearest to the ACS start point).
- **2017 mortgage** — Residential mortgages; 4 Apr 2017 taken from the 2018 ARA's prior-year comparative column (standalone 2017 ARA not catalogued). Consumer banking = unsecured lending (current-account overdrafts, personal loans, credit cards); Nationwide has no motor book. Allowance = balance-sheet impairment provision stock. Year-end 4 April (nearest to the ACS start point).
- **2017 unsecured_retail** — 4 Apr 2017 from the 2018 ARA comparative column. Consumer banking = unsecured lending (current-account overdrafts, personal loans, credit cards); Nationwide has no motor book. Allowance = balance-sheet impairment provision stock. Year-end 4 April (nearest to the ACS start point).
- **2018 mortgage** — Residential mortgages; last IAS 39 year (IFRS 9 adopted 5 Apr 2018). Consumer banking = unsecured lending (current-account overdrafts, personal loans, credit cards); Nationwide has no motor book. Allowance = balance-sheet impairment provision stock. Year-end 4 April (nearest to the ACS start point).
- **2018 unsecured_retail** — Last IAS 39 year. Consumer banking = unsecured lending (current-account overdrafts, personal loans, credit cards); Nationwide has no motor book. Allowance = balance-sheet impairment provision stock. Year-end 4 April (nearest to the ACS start point).
- **2019 mortgage** — Residential mortgages, amortised cost; first IFRS 9 year. A small FVTPL mortgage line (GBP72m, no impairment) is excluded. Consumer banking = unsecured lending (current-account overdrafts, personal loans, credit cards); Nationwide has no motor book. Allowance = balance-sheet impairment provision stock. Year-end 4 April (nearest to the ACS start point).
- **2019 unsecured_retail** — First IFRS 9 year (ECL, all stages). Consumer banking = unsecured lending (current-account overdrafts, personal loans, credit cards); Nationwide has no motor book. Allowance = balance-sheet impairment provision stock. Year-end 4 April (nearest to the ACS start point).
- **2022 mortgage** — Residential mortgages, amortised cost. A small FVTPL mortgage line (GBP64m, no impairment) is excluded. Consumer banking = unsecured lending (current-account overdrafts, personal loans, credit cards); Nationwide has no motor book. Allowance = balance-sheet impairment provision stock. Year-end 4 April (nearest to the ACS start point).
- **2022 unsecured_retail** — IFRS 9 ECL, all stages. Consumer banking = unsecured lending (current-account overdrafts, personal loans, credit cards); Nationwide has no motor book. Allowance = balance-sheet impairment provision stock. Year-end 4 April (nearest to the ACS start point).
- **2025 mortgage** — CAVEAT: FYE moved to 31 March 2025 (not 4 April); Group now consolidates the acquired Virgin Money, so mortgage book jumps to 275,890m and is NOT like-for-like with prior Nationwide-only years. Amortised cost; small FVTPL mortgage line (36m, no impairment) excluded. IFRS 9.
- **2025 unsecured_retail** — CAVEAT: 'Consumer lending' (relabelled from 'Consumer banking') jumps 4,263m->11,107m as it now folds in Virgin Money's unsecured book (cards/loans/overdrafts) - NOT like-for-like with prior years, and may include a small Virgin motor element. FYE 31 Mar 2025. IFRS 9.

### Santander UK

| ACS | Basis | Entity | Product | Allowance | Gross | Coverage | Source table | Page |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | IAS39 | Santander UK plc | mortgage | 593 | 148,079 | 0.4005% | Credit performance - mortgages (Impairment loan loss allowances) | printed p98 (PDF p100), 2013 AR |
| 2014 | IAS39 | Santander UK plc | unsecured_retail | 227 | 4,238 | 5.3563% | Credit performance - Banking & Consumer Credit | printed p104 (PDF p106), 2013 AR |
| 2015 | IAS39 | Santander UK Group Holdings plc | mortgage | 579 | 150,057 | 0.3859% | Credit performance - mortgages | printed p64 (PDF p66), 2014 AR |
| 2015 | IAS39 | Santander UK Group Holdings plc | unsecured_retail | 195 | 4,999 | 3.9008% | Credit performance - Banking & Consumer Credit | printed p71 (PDF p73), 2014 AR |
| 2016 | IAS39 | Santander UK plc | mortgage | 424 | 152,819 | 0.2775% | Credit performance - mortgages (Impairment loan loss allowances) | printed p69 (PDF p71), 2015 AR |
| 2016 | IAS39 | Santander UK plc | unsecured_retail | 188 | 5,571 | 3.3746% | Credit performance - vehicle/consumer & other unsecured finance | printed p76 (PDF p78), 2015 AR |
| 2017 | IAS39 | Santander UK plc | mortgage | 279 | 154,274 | 0.1808% | Credit performance - mortgages | printed p59 (PDF p61), 2016 AR |
| 2017 | IAS39 | Santander UK plc | unsecured_retail | 169 | 5,273 | 3.2050% | Credit performance - business banking, consumer finance & other unsecured | printed p65 (PDF p67), 2016 AR |
| 2018 | IAS39 | Santander UK plc | mortgage | 225 | 154,944 | 0.1452% | Credit performance - mortgages | printed p82 (PDF p84), 2017 opco AR |
| 2018 | IAS39 | Santander UK plc | unsecured_retail | 135 | 5,178 | 2.6072% | Credit performance - consumer (auto) finance & other unsecured (Total other unsecured) | printed p87 (PDF p89), 2017 opco AR |
| 2019 | IFRS9 | Santander UK plc | mortgage | 234 | 157,957 | 0.1481% | Credit performance - mortgages (Loss allowances) | printed p79 (PDF p81), 2018 AR |
| 2019 | IFRS9 | Santander UK plc | unsecured_retail | 220 | 5,640 | 3.9007% | Credit performance - consumer (auto) finance & other unsecured (Total other unsecured) | printed p83 (PDF p85), 2018 AR |
| 2022 | IFRS9 | Santander UK Group Holdings plc | mortgage | 191 | 177,297 | 0.1077% | Credit performance (audited) - mortgages (Loss allowances) | printed p131 (PDF p133), 2021 AR |
| 2022 | IFRS9 | Santander UK Group Holdings plc | unsecured_retail | 176 | 4,779 | 3.6828% | Credit performance (audited) - other unsecured (Total other unsecured) | printed p138 (PDF p140), 2021 AR |
| 2025 | IFRS9 | Santander UK plc | mortgage | 172 | 165,213 | 0.1041% | Credit performance (audited) - mortgages (Loss allowances) | printed p73 (PDF p75), 2024 AR |
| 2025 | IFRS9 | Santander UK plc | unsecured_retail | 270 | 5,299 | 5.0953% | Credit performance (audited) - other unsecured (Total other unsecured) | printed p78 (PDF p80), 2024 AR |

Notes:

- **2014 mortgage** — Mortgage gross incl. Social Housing loans and finance leases (footnote 2). IAS 39.
- **2014 unsecured_retail** — Unsecured = Bank Accounts/overdrafts (51/543) + Unsecured Personal Loans (90/2,016) + Credit Cards (86/1,679) = 227/4,238. Consumer Finance (auto, 85/3,145) and Business Banking (16/151) excluded. No printed subtotal that year; components summed. IAS 39.
- **2015 mortgage** — Mortgage gross incl. Social Housing/finance leases. Entity = Santander UK Group Holdings plc (became parent of Santander UK plc on 10 Jan 2014). IAS 39.
- **2015 unsecured_retail** — Unsecured = Overdrafts (46/544) + Personal Loans (76/2,208) + Credit Cards (73/2,247) = 195/4,999. Business Banking (14/155) and Consumer Finance (auto, 93/3,303) excluded. Components summed (no printed subtotal). IAS 39.
- **2016 mortgage** — Mortgage gross includes Social Housing loans and finance leases (footnote 2). IAS 39.
- **2016 unsecured_retail** — Unsecured = Personal loans (60/2,201) + Credit cards (86/2,834) + Overdrafts (42/536) = 188/5,571. Vehicle/auto (136/6,290) and Business banking (14/150) excluded. IAS 39.
- **2017 mortgage** — Mortgage gross incl. Social Housing/finance leases. IAS 39.
- **2017 unsecured_retail** — Unsecured = Personal (55/2,229) + Credit cards (77/2,493) + Overdrafts (37/551) = 169/5,273. Consumer/auto (146/6,764) and Business banking (57/2,327) excluded. IAS 39.
- **2018 mortgage** — Mortgage gross incl. Social Housing/finance leases. IAS 39. FY2017 opco AR located by search (not catalogued).
- **2018 unsecured_retail** — Unsecured = printed 'Total other unsecured' = Personal (44/2,169) + Credit cards (62/2,444) + Overdrafts (29/565) = 135/5,178. Consumer (auto) finance (77/6,957) excluded. IAS 39.
- **2019 mortgage** — IFRS 9 ECL, all stages, on+off balance sheet (per footnote; off-balance ~GBP3m). Mortgage gross incl. Social Housing/finance leases.
- **2019 unsecured_retail** — Unsecured = 'Total other unsecured' = Personal (47/2,182) + Credit cards (112/2,865) + Overdrafts (61/593) = 220/5,640. Consumer (auto) finance (85/7,347) excluded. IFRS 9 ECL.
- **2022 mortgage** — IFRS 9 ECL, all stages, on+off balance sheet. Entity = Santander UK Group Holdings plc (vs Santander UK plc opco used for 2016-2019 ACS).
- **2022 unsecured_retail** — Unsecured = 'Total other unsecured' = Personal (47/2,000) + Credit cards (89/2,341) + Overdrafts (40/438) = 176/4,779. Business banking (22/3,532) excluded; consumer/auto is a separate table. IFRS 9 ECL.
- **2025 mortgage** — IFRS 9 ECL, on+off balance sheet. Mortgage gross = RBB Mortgages portfolio.
- **2025 unsecured_retail** — Unsecured = 'Total other unsecured' = Personal (63/2,089) + Credit cards (150/2,774) + Overdrafts (57/436) = 270/5,299. Business banking (16/1,212) and consumer/auto (separate) excluded. IFRS 9 ECL, on+off balance sheet.

### The Royal Bank of Scotland Group

| ACS | Basis | Entity | Product | Allowance | Gross | Coverage | Source table | Page |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | IAS39 | The Royal Bank of Scotland Group plc | mortgage | 1,799 | 148,533 | 1.2112% | Sector and geographical concentration (Credit risk): Personal - mortgages | FY2013 Form 20-F (~p295) |
| 2014 | IAS39 | The Royal Bank of Scotland Group plc | unsecured_retail | 1,909 | 28,160 | 6.7791% | Sector and geographical concentration (Credit risk): Personal - unsecured | FY2013 Form 20-F (~p295) |
| 2015 | IAS39 | The Royal Bank of Scotland Group plc | mortgage | 1,521 | 150,572 | 1.0101% | Sector and geographical concentration (Credit risk): Personal - mortgages | FY2014 Form 20-F (~p285) |
| 2015 | IAS39 | The Royal Bank of Scotland Group plc | unsecured_retail | 1,585 | 29,155 | 5.4365% | Sector and geographical concentration (Credit risk): Personal - unsecured | FY2014 Form 20-F (~p285) |
| 2016 | IAS39 | The Royal Bank of Scotland Group plc | mortgage | 1,006 | 137,601 | 0.7311% | Sector and geographical concentration (Credit risk): Personal - mortgages (1) | FY2015 Form 20-F |
| 2016 | IAS39 | The Royal Bank of Scotland Group plc | unsecured_retail | 1,151 | 16,654 | 6.9113% | Sector and geographical concentration (Credit risk): Personal - unsecured | FY2015 Form 20-F |
| 2017 | IAS39 | The Royal Bank of Scotland Group plc | mortgage | 1,019 | 153,319 | 0.6646% | Sector and geographical concentration (Credit risk): Personal - mortgages | printed p338, FY2016 Form 20-F |
| 2017 | IAS39 | The Royal Bank of Scotland Group plc | unsecured_retail | 900 | 14,492 | 6.2103% | Sector and geographical concentration (Credit risk): Personal - unsecured | printed p338, FY2016 Form 20-F |
| 2018 | IAS39 | The Royal Bank of Scotland Group plc | mortgage | 994 | 163,010 | 0.6098% | Sector and geographical concentration (Credit risk): Personal - mortgages (1) | FY2017 Form 20-F |
| 2018 | IAS39 | The Royal Bank of Scotland Group plc | unsecured_retail | 763 | 14,587 | 5.2307% | Sector and geographical concentration (Credit risk): Personal - unsecured | FY2017 Form 20-F |
| 2019 | IFRS9 | The Royal Bank of Scotland Group plc | mortgage | 839 | 165,081 | 0.5082% | Portfolio summary - sector analysis (audited): Personal / Mortgages | printed p137, FY2018 Form 20-F |
| 2019 | IFRS9 | The Royal Bank of Scotland Group plc | unsecured_retail | 958 | 13,794 | 6.9450% | Portfolio summary - sector analysis (audited): Personal / Credit cards + Other personal | printed p137, FY2018 Form 20-F |
| 2022 | IFRS9 | NatWest Group plc | mortgage | 768 | 194,011 | 0.3959% | Sector analysis - portfolio summary (audited): Loans / ECL provisions by geography | printed p221 (PDF p112), 2021 ARA |
| 2022 | IFRS9 | NatWest Group plc | unsecured_retail | 1,174 | 13,369 | 8.7815% | Sector analysis - portfolio summary (audited): Loans / ECL provisions by geography | printed p221 (PDF p112), 2021 ARA |
| 2025 | IFRS9 | NatWest Group plc | mortgage | 462 | 209,846 | 0.2202% | Sector analysis - portfolio summary (audited): Personal / Mortgages | printed p203, 2024 ARA |
| 2025 | IFRS9 | NatWest Group plc | unsecured_retail | 1,350 | 16,679 | 8.0940% | Sector analysis - portfolio summary (audited): Personal / Credit cards + Other personal | printed p203, 2024 ARA |

Notes:

- **2014 mortgage** — Group consolidated (mortgage book 148,533m incl. RoI/Ulster). High coverage (1.2%) is the distressed Irish book at its 2013 trough; printed provisions-as-%-of-gross = 1.2%. IAS 39.
- **2014 unsecured_retail** — 'Personal - unsecured' = credit cards + personal loans + overdrafts (footnote 'Includes instalment credit'); excludes finance leases/motor. Provisions = IAS 39 balance-sheet allowance stock; printed provisions-as-%-of-gross confirms.
- **2015 mortgage** — Group consolidated (mortgage book 150,572m). Printed prov-%-gross = 1.0%. IAS 39. Note: FY2015 onward drops ~13bn on the Citizens (US) deconsolidation.
- **2015 unsecured_retail** — 'Personal - unsecured' = credit cards + personal loans + overdrafts (footnote 'Includes instalment credit'); excludes finance leases/motor. Provisions = IAS 39 balance-sheet allowance stock; printed provisions-as-%-of-gross confirms.
- **2016 mortgage** — Group consolidated (mortgage book 137,601m as-reported; = UK 123,653 + RoI 13,908). Step down from FY2014 reflects Citizens deconsolidation. Printed prov-%-gross = 0.7%. IAS 39.
- **2016 unsecured_retail** — 'Personal - unsecured' = credit cards + personal loans + overdrafts (footnote 'Includes instalment credit'); excludes finance leases/motor. Provisions = IAS 39 balance-sheet allowance stock; printed provisions-as-%-of-gross confirms.
- **2017 mortgage** — Group consolidated (mortgage book 153,319m incl. Ulster/Ireland; total customer loans 327,478m). Provisions = IAS 39 balance-sheet allowance stock (not the P&L charge). Printed 'provisions as % of gross' = 0.7% matches. Higher than peers due to distressed Irish/Ulster tail.
- **2017 unsecured_retail** — 'Personal - unsecured' is a single IAS 39 line = credit cards + personal loans + overdrafts; excludes 'Finance leases and instalment credit' (12,269m, separate), so no motor. Printed 'provisions as % of gross' = 6.2% matches.
- **2018 mortgage** — Group consolidated (mortgage book 163,010m = UK 147,399 + RoI 15,572). Printed prov-%-gross = 0.6%. IAS 39.
- **2018 unsecured_retail** — 'Personal - unsecured' = credit cards + personal loans + overdrafts (footnote 'Includes instalment credit'); excludes finance leases/motor. Provisions = IAS 39 balance-sheet allowance stock; printed provisions-as-%-of-gross confirms.
- **2019 mortgage** — Group consolidated (mortgage book 165,081m; UK 150,233m) - not the ~24bn ring-fenced RBS plc slice. Allowance = total ECL stock, all stages. Mortgages include ~0.7bn Private Banking secured per ECL methodology. IFRS 9.
- **2019 unsecured_retail** — Unsecured = Credit cards (230/4,216) + Other personal (728/9,578) = 958/13,794. 'Other personal' = unsecured personal loans/overdrafts; no motor/secured in these lines. IFRS 9 ECL, all stages.
- **2022 mortgage** — Mortgages. Gross = loans gross of ECL; allowance = total ECL provisions (Stages 1-3). NatWest Group consolidated.
- **2022 unsecured_retail** — Unsecured = Credit cards (260/3,947) + Other personal (914/9,422); allowance 1,174m, gross 13,369m. 'Other personal' = unsecured personal loans/overdrafts; no motor line. IFRS 9.
- **2025 mortgage** — Group consolidated (mortgage book 209,846m). Allowance = total ECL, all stages. IFRS 9.
- **2025 unsecured_retail** — Unsecured = Credit cards (381/6,930) + Other personal (969/9,749) = 1,350/16,679. No motor in the Personal columns. IFRS 9 ECL, all stages.

---

*Cross-check:* the static FY2019-vintage snapshot `firm_provisions.csv` agrees to order of magnitude where it overlaps; Nationwide's 4 Apr 2019 figures (mortgage 0.111%, unsecured 9.11%) match it to the basis point.

