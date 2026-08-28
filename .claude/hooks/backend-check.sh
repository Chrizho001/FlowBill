#!/usr/bin/env bash
set -e

# ==============================================================================
# FlowBill — Backend Verification Hook for Claude Code
# Runs Django system checks, migration drift detection, and targeted Pytest
# ==============================================================================

FILE_PATH="$1"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
FLOWBILL_DIR="$REPO_ROOT/flowbill"

# Only run if a backend file was touched or if invoked without arguments
if [ -z "$FILE_PATH" ] || [[ "$FILE_PATH" =~ flowbill/ ]]; then
    echo ""
    echo "========================================="
    echo "🔍 FlowBill Backend Hook: Checking..."
    echo "========================================="

    cd "$FLOWBILL_DIR"

    # 1. Django Configuration & Syntax Check
    echo "▶ Checking Django system integrity..."
    if ! uv run python manage.py check; then
        echo "❌ Django system check failed. Please fix the configuration or syntax error."
        exit 1
    fi

    # 2. Check for missing migrations if models.py was touched
    if [ -z "$FILE_PATH" ] || [[ "$FILE_PATH" =~ models\.py ]]; then
        echo "▶ Checking for ungenerated model migrations..."
        if ! uv run python manage.py makemigrations --check --dry-run; then
            echo "⚠️ Warning: Detected model changes without a migration!"
            echo "Please run: 'uv run python manage.py makemigrations'"
        fi
    fi

    # 3. Run Targeted or Full Pytest Suite
    if [[ "$FILE_PATH" =~ apps/([^/]+)/ ]]; then
        APP_NAME="${BASH_REMATCH[1]}"
        if [ -d "$FLOWBILL_DIR/apps/$APP_NAME/tests" ]; then
            echo "▶ Running targeted tests for apps/$APP_NAME..."
            uv run python -m pytest "apps/$APP_NAME/tests" --no-cov
        else
            echo "▶ Running full test suite..."
            uv run python -m pytest --no-cov
        fi
    else
        echo "▶ Running targeted/full tests..."
        uv run python -m pytest --no-cov
    fi

    echo "✅ Backend checks passed successfully!"
    echo ""
fi
