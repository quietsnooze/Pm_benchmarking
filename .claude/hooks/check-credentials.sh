#!/bin/bash
# Credential / secrets exfiltration check.
#
# Runs as a Claude Code PreToolUse hook on Bash. It scans the staged
# (and, for `git commit -a`, the tracked-unstaged) diff for common
# credential patterns and blocks the commit if any are found.
#
# Input:  hook JSON on stdin (see docs)
# Output: JSON on stdout to allow/deny the tool call.

set -uo pipefail

input=$(cat)
command=$(printf '%s' "$input" | jq -r '.tool_input.command // ""' 2>/dev/null || echo "")

# Only scan git commit commands (including chained ones like `git add . && git commit -m ...`)
if ! printf '%s' "$command" | grep -qE '(^|[[:space:]&|;(`])git[[:space:]]+commit([[:space:]]|$)'; then
  exit 0
fi

# Move to repo root; silently skip if not in a git repo
repo_root=$(git rev-parse --show-toplevel 2>/dev/null) || exit 0
cd "$repo_root"

# Detect `git commit -a` / `--all` variants, which auto-stage tracked files.
# In that case we also need to scan unstaged changes to tracked files,
# since at hook time those haven't been staged yet.
if printf '%s' "$command" | grep -qE '(^|[[:space:]])git[[:space:]]+commit[[:space:]]+[^#]*(-[a-zA-Z]*a[a-zA-Z]*([[:space:]]|$|=)|--all([[:space:]]|$|=))'; then
  raw_diff=$(git diff HEAD 2>/dev/null)
  name_list=$(git diff HEAD --name-only 2>/dev/null)
else
  raw_diff=$(git diff --cached 2>/dev/null)
  name_list=$(git diff --cached --name-only 2>/dev/null)
fi

if [ -z "$raw_diff" ]; then
  exit 0
fi

# Only scan added lines (leading +), skipping the +++ file header lines.
added=$(printf '%s\n' "$raw_diff" | grep -E '^\+' | grep -vE '^\+\+\+')

findings=()

scan() {
  local label="$1"
  local pattern="$2"
  if printf '%s' "$added" | grep -qE "$pattern"; then
    findings+=("$label")
  fi
}

# --- Cloud / provider credentials ---
scan "AWS Access Key ID"            'AKIA[0-9A-Z]{16}'
scan "AWS Secret Access Key"        'aws_secret_access_key[[:space:]]*=[[:space:]]*["'"'"']?[A-Za-z0-9/+=]{40}'
scan "GitHub Personal Access Token" 'gh[pousr]_[A-Za-z0-9]{36,}'
scan "GitHub Fine-grained PAT"      'github_pat_[A-Za-z0-9_]{80,}'
scan "Google API Key"               'AIza[0-9A-Za-z_-]{35}'
scan "GCP Service Account JSON"     '"type"[[:space:]]*:[[:space:]]*"service_account"'
scan "Slack token"                  'xox[baprs]-[A-Za-z0-9-]{10,}'
scan "Stripe Live Secret Key"       'sk_live_[0-9a-zA-Z]{24,}'
scan "Anthropic API Key"            'sk-ant-[A-Za-z0-9_-]{20,}'
scan "OpenAI API Key"               'sk-[A-Za-z0-9]{48}'

# --- Generic secret material ---
scan "Private key block"            'BEGIN[[:space:]]+(RSA[[:space:]]+|DSA[[:space:]]+|EC[[:space:]]+|OPENSSH[[:space:]]+|PGP[[:space:]]+)?PRIVATE KEY'
scan "JWT token"                    'eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}'
scan "Hardcoded password/secret"    '(password|passwd|pwd|secret|api[_-]?key|access[_-]?token|auth[_-]?token)[[:space:]]*[:=][[:space:]]*["'"'"'][^"'"'"'[:space:]]{8,}["'"'"']'

# --- Flag .env-style files (but allow .env.example / .env.sample / .env.template) ---
env_hits=$(printf '%s\n' "$name_list" | grep -E '(^|/)\.env($|\.)' | grep -vE '\.(example|sample|template)$' || true)
if [ -n "$env_hits" ]; then
  findings+=(".env file being committed: $(printf '%s' "$env_hits" | tr '\n' ' ')")
fi

if [ ${#findings[@]} -eq 0 ]; then
  exit 0
fi

reason=$'Credential check FAILED. The staged diff appears to contain potential secrets:\n'
for f in "${findings[@]}"; do
  reason+="  - $f"$'\n'
done
reason+=$'\nReview with: git diff --cached\nRemove any real secrets before committing. If this is a false positive, you can temporarily disable the hook in .claude/settings.json or move the value to an environment variable / .env file (gitignored).'

jq -n --arg reason "$reason" '{
  hookSpecificOutput: {
    hookEventName: "PreToolUse",
    permissionDecision: "deny",
    permissionDecisionReason: $reason
  }
}'
exit 0
