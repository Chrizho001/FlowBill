#!/usr/bin/env bash
set -e

# ==============================================================================
# FlowBill — Secret Scanner Hook for Claude Code
# Prevents accidental hardcoding of live/test API keys, private keys, or tokens
# ==============================================================================

FILE_PATH="$1"

if [ -n "$FILE_PATH" ] && [ -f "$FILE_PATH" ]; then
    # Exclude .env files, git directories, node_modules, and lockfiles
    if [[ "$FILE_PATH" =~ \.env ]] || [[ "$FILE_PATH" =~ \.git/ ]] || [[ "$FILE_PATH" =~ node_modules/ ]] || [[ "$FILE_PATH" =~ \.lock ]]; then
        exit 0
    fi

    # Patterns: Paystack keys, GitHub tokens, Private keys, AWS keys
    if grep -E -n -q '(sk_live_[a-zA-Z0-9]{20,}|sk_test_[a-zA-Z0-9]{20,}|ghp_[a-zA-Z0-9]{20,}|-----BEGIN PRIVATE KEY-----|AKIA[0-9A-Z]{16})' "$FILE_PATH"; then
        echo ""
        echo "========================================="
        echo "🚨 SECURITY HOOK: Hardcoded Secret Detected!"
        echo "========================================="
        echo "File: $FILE_PATH"
        echo "Matches potential sensitive credential or API key."
        echo "Please use decouple/environment variables instead."
        echo ""
        exit 1
    fi
fi
