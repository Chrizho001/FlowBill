#!/usr/bin/env bash
# ==============================================================================
# Master Hook Runner for Claude Code (PostToolUse)
# Reads tool JSON from stdin, extracts the edited file path, and runs:
#   1. secret-scanner.sh  → hard stop on failure (exit 2 immediately)
#   2. backend-check.sh   → run + report together with #3
#   3. frontend-check.sh  → run + report together with #2
# ==============================================================================
set -uo pipefail  # no -e: we want checks 2 & 3 to both run even if one fails

HOOKS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INPUT=$(cat)

if ! command -v jq >/dev/null 2>&1; then
  echo "run-all-checks.sh: 'jq' is required but not installed" >&2
  exit 2
fi

FILE_PATH=$(jq -r '.tool_input.file_path // empty' <<< "$INPUT")
[[ -z "$FILE_PATH" ]] && exit 0

# --- 1. Secret scanner: hard stop, don't waste time on anything else ---
if [[ -f "$HOOKS_DIR/secret-scanner.sh" ]]; then
  if ! bash "$HOOKS_DIR/secret-scanner.sh" "$FILE_PATH"; then
    echo "SECURITY: secret-scanner failed for $FILE_PATH — fix this before anything else." >&2
    exit 2
  fi
fi

# --- 2 & 3. Backend + frontend: run both, report together ---
FAILED=0
FAIL_MSGS=()

run_check() {
  local name="$1" script="$2"
  if [[ -f "$script" ]] && ! bash "$script" "$FILE_PATH"; then
    FAILED=1
    FAIL_MSGS+=("$name failed for $FILE_PATH")
  fi
}

run_check "backend-check" "$HOOKS_DIR/backend-check.sh"
run_check "frontend-check" "$HOOKS_DIR/frontend-check.sh"

if [[ "$FAILED" -eq 1 ]]; then
  printf '%s\n' "${FAIL_MSGS[@]}" >&2
  exit 2
fi

exit 0