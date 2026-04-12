#!/bin/bash
# Fast lint + format check + pytest wrapper.
# Usage: ./scripts/check.sh [file_or_directory]
# Note: Run from the project root. The check.ts tool sets cwd automatically.

TARGET=${1:-src/}

echo "=== Ruff lint: $TARGET ==="
ruff check "$TARGET" 2>&1 || true

echo ""
echo "=== Ruff format check: $TARGET ==="
ruff format --check "$TARGET" 2>&1 || true

if [ -d "tests" ] && [ -z "$1" ]; then
    echo ""
    echo "=== Pytest ==="
    python3 -m pytest tests/ -q 2>&1 || true
fi
