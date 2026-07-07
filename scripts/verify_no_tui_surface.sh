#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

fail() {
    printf 'TUI surface verification failed: %s\n' "$1" >&2
    exit 1
}

if [ -e "tui_manager.py" ]; then
    fail "tui_manager.py exists in the supported runtime root"
fi

if find . \
    -path './.git' -prune -o \
    -path './management' -prune -o \
    -path './__pycache__' -prune -o \
    \( -name 'tui_manager.py' -o -name 'Start-TUI.bat' \) -print | grep -q .; then
    find . \
        -path './.git' -prune -o \
        -path './management' -prune -o \
        -path './__pycache__' -prune -o \
        \( -name 'tui_manager.py' -o -name 'Start-TUI.bat' \) -print >&2
    fail "active TUI entrypoint found"
fi

if grep -RInE '(^|[[:space:]])(from|import)[[:space:]]+(textual|rich)([[:space:].]|$)' \
    -- profile_manager.py install.sh README.md scripts 2>/dev/null; then
    fail "Textual/Rich import found in supported files"
fi

printf 'TUI surface verification passed.\n'
