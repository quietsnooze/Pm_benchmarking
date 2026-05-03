"""End-to-end ingest: rebuild ``processed_inputs/`` from ``raw_inputs/``.

This is the project's "build" entrypoint for data. It runs the two ingest
steps in order:

1. :mod:`uk_stress_benchmark.sync_sources` — download any raw files declared
   in ``SOURCES.md`` that aren't already in ``raw_inputs/``.
2. :mod:`uk_stress_benchmark.extract_appendix_tables` — parse the
   bank-specific impairment-charge tables out of the BoE results PDFs into
   one CSV per table under ``processed_inputs/``.

Both steps are idempotent, so re-running ``uv run ingest`` after a fresh
clone (with raw_inputs/ empty) reproduces the full processed dataset.
"""

from __future__ import annotations

from uk_stress_benchmark import extract_appendix_tables, sync_sources


def main() -> None:
    print("== sync-sources ==")
    sync_sources.main()
    print()
    print("== extract-tables ==")
    extract_appendix_tables.main()


if __name__ == "__main__":
    main()
