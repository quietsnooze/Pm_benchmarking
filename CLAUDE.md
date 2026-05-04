# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Pm_benchmarking is a Python rewrite of a legacy R analysis: UK banking-system stress-test benchmarking against Bank of England ACS scenarios (2014–2019). The end product is a **Streamlit web app** deployed to Streamlit Community Cloud, intended as a public portfolio piece linkable from Pete's LinkedIn. The repo will be renamed `uk-stress-test-benchmarking` when first pushed publicly — until then it lives under its working name.

The legacy R code under [old_version/stress test benchmarks/](old_version/stress test benchmarks/) is **reference only**. Read it to understand the methodology being ported (BoE workbook ingest → low-point shock features → per-product linear models with optional stepwise selection). Do not extend, refactor, or "tidy" it.

## Toolchain

Python project, managed with **uv**. Migrated from pip on 2026-05-01 once Pete was past the "learn classic Python packaging" stage. Lockfile (`uv.lock`) is committed; `.venv` is gitignored.

| Purpose | Command |
| --- | --- |
| Install / sync deps | `uv sync --extra dev` |
| Run tests | `uv run pytest` |
| Run a single test | `uv run pytest path/to/test_x.py::test_name` |
| Lint | `uv run ruff check` |
| Format | `uv run ruff format` |
| Type check | `uv run pyright` |
| Local dev server | `uv run streamlit run app.py` |
| Add a runtime dependency | `uv add <pkg>` |
| Add a dev dependency | `uv add --optional dev <pkg>` |
| Update a single dependency | `uv lock --upgrade-package <pkg>` |
| Re-resolve everything | `uv lock --upgrade` |

### Data ingest commands

The data pipeline is split into two idempotent steps plus an "all" wrapper, all exposed as console scripts via `[project.scripts]` in `pyproject.toml`:

| Purpose | Command |
| --- | --- |
| Download raw inputs declared in [SOURCES.md](SOURCES.md) into `raw_inputs/` | `uv run sync-sources` |
| Parse BoE results-PDF impairment-charge tables to CSVs in `processed_inputs/` | `uv run extract-tables` |
| Flatten BoE variable-paths workbooks (base / ACS / BES / non-participants) to CSVs in `processed_inputs/` | `uv run extract-scenarios` |
| All three, in order — equivalent to a "build" of `processed_inputs/` from scratch | `uv run ingest` |

`raw_inputs/` is gitignored (raw files reproducible from `SOURCES.md`); `processed_inputs/` **is** committed so a fresh clone has the analysis-ready CSVs without needing to re-run ingest.

`uv run` automatically syncs the venv before each command, so there's no separate "activate" step. Activating the venv manually (`.venv\Scripts\Activate.ps1`) still works if you want to call binaries directly.

**Streamlit Community Cloud deploy:** if SCC doesn't pick up `uv.lock` directly, export pinned requirements with `uv export --no-dev -o requirements.txt` and commit (or generate at deploy time).

**Environment gotcha (this machine):** Pete has a system-wide `VIRTUAL_ENV` set, which makes uv emit a warning on every run. Harmless, but if it's annoying, `Remove-Item Env:VIRTUAL_ENV` for the current session or unset it in his PowerShell profile.

## Design directives

These shape every code change in this repo and are non-negotiable defaults:

1. **Deep modules, narrow interfaces** (Ousterhout, *A Philosophy of Software Design*). Each module should hide substantial implementation behind a small public surface. Avoid shallow wrappers, pass-through helpers, "utils" grab-bags, and one-line modules. Justify a module by what it hides, not what it exposes. This is the explicit upgrade Pete wants over the legacy R code.
2. **TDD for new logic.** Red → green → refactor. The TDD workflow is codified in [.claude/skills/tdd/](.claude/skills/tdd/) (with reference docs on deep modules, interface design, mocking, refactoring, and tests). Follow that skill rather than improvising a parallel process. The Streamlit UI layer is exempt: test the underlying functions it calls, not the rendering.

Other available skills in [.claude/skills/](.claude/skills/): `grill-me` (interview-style design stress-test), `write-a-prd` (PRD authoring via interview + codebase exploration), `prd-to-issues` (decompose a PRD into vertical-slice GitHub issues).

## Data handling

Raw source files (BoE scenario workbooks, EBA disclosures, Pillar 3 spreadsheets, DFAST results) are kept **locally only** in [raw_inputs/](raw_inputs/) and must not be committed — they're large and reproducible from public sources. The repo commits:

- A `SOURCES.md` recording where each raw file came from (URL, publication date) — to be created. Update it whenever a new raw file is added or replaced.
- Processed datasets under [processed_inputs/](processed_inputs/), preferably as Parquet. These are small enough for Streamlit Community Cloud to load on cold start.

Ingest scripts process `raw_inputs/` → `processed_inputs/`. The deployed app reads only `processed_inputs/`. Confirm `.gitignore` excludes `raw_inputs/` before any data lands there — the current `.gitignore` is a default Python template and does not.

## Pre-commit credential scan

A `PreToolUse` hook in [.claude/settings.json](.claude/settings.json) runs [.claude/hooks/check-credentials.sh](.claude/hooks/check-credentials.sh) before any Bash call that contains `git commit`. It scans the staged diff (or `HEAD` diff for `commit -a`) for AWS keys, GitHub PATs, Anthropic/OpenAI keys, private-key blocks, JWTs, and `.env` files, and blocks the commit if any match. If a commit is rejected and the finding is a false positive, fix the regex or move the value to a gitignored `.env` rather than disabling the hook.

## Hard rules

- **Never edit, create, or delete files outside this repository's directory.** Reads outside are fine; writes are not. If something outside needs changing (global tool config, sibling repos, dotfiles), surface it to Pete — don't act.
- The legacy R code under [old_version/](old_version/) is read-only reference. Don't touch it.

## Working with Pete

Pete is coming from R and actively learning Python. When introducing a Python pattern that has an R analogue, briefly explain the *why* (e.g. tidyverse `%>%` → method chains; Shiny reactives → Streamlit `st.session_state`). Drop the explanations as he picks each pattern up.
