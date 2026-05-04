"""End-to-end ingest: rebuild ``processed_inputs/`` from ``raw_inputs/``.

This is the project's "build" entrypoint for data. It runs four ingest steps
in order:

1. :mod:`uk_stress_benchmark.sync_sources` — download any raw files declared
   in ``SOURCES.md`` that aren't already in ``raw_inputs/``.
2. :mod:`uk_stress_benchmark.extract_appendix_tables` — parse the
   bank-specific impairment-charge tables out of the BoE results PDFs into
   one CSV per table under ``processed_inputs/``.
3. :mod:`uk_stress_benchmark.extract_scenarios` — flatten the BoE
   variable-paths workbooks (one per ACS year, plus the 2019 non-
   participants sheet) into per-scenario CSVs under ``processed_inputs/``.
4. :mod:`uk_stress_benchmark.aggregate_firm_results` — consolidate the
   per-table impairment-charge CSVs from step 2 into a single tidy
   ``firm_results.csv`` (one row per firm × ACS year, decimal-encoded).

All steps are idempotent, so re-running ``uv run ingest`` after a fresh
clone (with raw_inputs/ empty) reproduces the full processed dataset.
"""

from __future__ import annotations

from uk_stress_benchmark import (
    aggregate_firm_results,
    extract_appendix_tables,
    extract_scenarios,
    sync_sources,
)


def main() -> None:
    print("== sync-sources ==")
    sync_sources.main()
    print()
    print("== extract-tables ==")
    extract_appendix_tables.main()
    print()
    print("== extract-scenarios ==")
    extract_scenarios.main()
    print()
    print("== aggregate-firm-results ==")
    aggregate_firm_results.main()


if __name__ == "__main__":
    main()
