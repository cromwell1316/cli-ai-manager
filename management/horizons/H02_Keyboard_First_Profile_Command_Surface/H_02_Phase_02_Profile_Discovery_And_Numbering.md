# H_02 Phase 02 Profile Discovery And Numbering

Owner: cli-profile-manager
Source of Truth: management/horizons/H02_Keyboard_First_Profile_Command_Surface/README.md
Lifecycle: living
Document Class: phase

Status: planned.

## Scope

Separate display slots from existing profiles and fix default target numbers.

## Required Behavior

- Existing profiles are discovered from actual `pN` directories and credential
  files.
- Empty display slots can be shown without becoming "existing profiles".
- Add/import chooses the first free positive integer.
- Explicit profile numbers are validated as positive integers.

## Phase Exit

An empty install defaults to `p1`; if `p1` and `p3` exist, add/import defaults to
`p2`.
