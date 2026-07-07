# H_00 Horizon Brief

Owner: cli-profile-manager
Source of Truth: management/horizons/H02_Keyboard_First_Profile_Command_Surface/README.md
Lifecycle: living
Document Class: horizon brief

Status: planned.

## Problem

The current pure Python manager is dependency-light but still menu-first. Common
operations require repeated navigation, and the profile discovery code reserves
`p1..p12`, which makes add/import defaults jump to `p13`.

## Desired Outcome

A keyboard-first CLI provides direct commands and a minimal selector. Frequent
actions are reachable with one command or one key sequence, have predictable exit
codes, and can be tested without a terminal UI harness.

## Success Criteria

- `ai-man list agy`, `ai-man launch agy p2`, `ai-man import agy ...`, and
  equivalent commands exist.
- Add/import default to the first free profile number.
- Commands return non-zero on missing executable, missing token, invalid profile,
  and import parse errors.
- Interactive selector remains usable with arrows, digits, Enter, Esc/q, and no
  third-party dependencies.
