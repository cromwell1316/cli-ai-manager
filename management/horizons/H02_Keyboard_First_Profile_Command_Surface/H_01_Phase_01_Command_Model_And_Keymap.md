# H_01 Phase 01 Command Model And Keymap

Owner: cli-profile-manager
Source of Truth: management/horizons/H02_Keyboard_First_Profile_Command_Surface/README.md
Lifecycle: living
Document Class: phase

Status: planned.

## Scope

Define the command grammar and keyboard shortcuts before implementation.

## Command Model

- `ai-man list <tool>`
- `ai-man status <tool> [profile]`
- `ai-man launch <tool> <profile> [-- args...]`
- `ai-man login <tool> [profile]`
- `ai-man import <tool> <path> [profile]`
- `ai-man export <tool> <profile> [--to path]`
- `ai-man label <tool> <profile> <label>`
- `ai-man clear <tool> <profile>`
- `ai-man sync [--from wsl|windows] [--mode soft|hard]`

## Keymap

- Digits select visible profiles.
- Arrow keys move selection.
- Enter launches.
- `a` login/add, `i` import, `e` export, `l` label, `s` status, `c` clear,
  `q`/Esc exit.

## Phase Exit

README and help output describe the same commands and keys.
