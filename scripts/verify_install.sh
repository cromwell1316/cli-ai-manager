#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BIN_DIR="${AI_MAN_INSTALL_BIN_DIR:-$HOME/.local/bin}"
TARGET="$PROJECT_DIR/profile_manager.py"
ALIASES=(ai-man profile-man pman)

fail() {
    printf 'install verification failed: %s\n' "$*" >&2
    exit 1
}

[ -x "$TARGET" ] || fail "$TARGET is not executable"

for name in "${ALIASES[@]}"; do
    link="$BIN_DIR/$name"
    [ -L "$link" ] || fail "$link is not a symlink"
    resolved="$(readlink -f "$link")"
    expected="$(readlink -f "$TARGET")"
    [ "$resolved" = "$expected" ] || fail "$link points to $resolved, expected $expected"
done

if command -v ai-man >/dev/null 2>&1; then
    resolved_cmd="$(readlink -f "$(command -v ai-man)")"
    expected="$(readlink -f "$TARGET")"
    [ "$resolved_cmd" = "$expected" ] || fail "PATH ai-man resolves to $resolved_cmd, expected $expected"
else
    printf 'warning: ai-man is not on PATH; add %s to PATH\n' "$BIN_DIR" >&2
fi

printf 'install verification passed: aliases point at %s\n' "$TARGET"
