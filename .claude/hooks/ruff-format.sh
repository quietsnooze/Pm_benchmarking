#!/bin/bash
# Auto-format + lint-fix Python files after Claude edits them.
#
# Runs as a Claude Code PostToolUse hook on Edit / MultiEdit / Write. It reads
# the edited file path from the hook payload and, if it's a Python file, runs
# `ruff format` then `ruff check --fix` on just that file so the working tree
# stays formatted and import-sorted without manual "ran ruff at the end" churn.
#
# This is non-blocking: it never fails the tool call. Any lint findings that
# ruff could not auto-fix are surfaced back to Claude as additional context
# (not an error) so they can be addressed in-flow.
#
# Input:  hook JSON on stdin (see docs)
# Output: optional JSON on stdout with PostToolUse additionalContext.

set -uo pipefail

input=$(cat)
file_path=$(printf '%s' "$input" | jq -r '.tool_input.file_path // ""' 2>/dev/null || echo "")

# Only act on existing Python files.
case "$file_path" in
  *.py) ;;
  *) exit 0 ;;
esac
[ -f "$file_path" ] || exit 0

# Run from repo root so ruff picks up pyproject.toml config.
repo_root=$(git rev-parse --show-toplevel 2>/dev/null) || exit 0
cd "$repo_root"

# Format, then apply safe lint autofixes (import sorting, simple rewrites, etc.).
uv run ruff format "$file_path" >/dev/null 2>&1
uv run ruff check --fix "$file_path" >/dev/null 2>&1

# Report anything ruff still flags, without blocking the edit. `--quiet`
# suppresses the "All checks passed!" summary so we only surface real findings.
remaining=$(uv run ruff check --quiet "$file_path" 2>/dev/null)
if [ -n "$remaining" ]; then
  jq -n --arg ctx "ruff reformatted ${file_path}, but some lint findings remain (not auto-fixable):"$'\n'"$remaining" '{
    hookSpecificOutput: {
      hookEventName: "PostToolUse",
      additionalContext: $ctx
    }
  }'
fi
exit 0
