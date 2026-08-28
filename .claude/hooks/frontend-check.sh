#!/usr/bin/env bash
set -e

# ==============================================================================
# FlowBill — Frontend Verification Hook for Claude Code
# Runs TypeScript compiler check to prevent type errors in Next.js/React
# ==============================================================================

FILE_PATH="$1"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
FRONTEND_DIR="$REPO_ROOT/frontend"

# Only run if a frontend file was touched
if [ -n "$FILE_PATH" ] && [[ "$FILE_PATH" =~ frontend/ ]]; then
    echo ""
    echo "========================================="
    echo "🔍 FlowBill Frontend Hook: Checking..."
    echo "========================================="

    cd "$FRONTEND_DIR"

    echo "▶ Running TypeScript type check (tsc --noEmit)..."
    if npx tsc --noEmit; then
        echo "✅ TypeScript check passed with 0 errors!"
    else
        echo "❌ TypeScript check failed. Please fix the type errors above."
        exit 1
    fi
    echo ""
fi
