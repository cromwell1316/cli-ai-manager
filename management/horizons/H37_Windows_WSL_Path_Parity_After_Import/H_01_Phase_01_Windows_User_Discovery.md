# H_01 Phase 01 Windows User Discovery

Owner: cli-profile-manager
Source of Truth: management/horizons/H37_Windows_WSL_Path_Parity_After_Import/README.md
Lifecycle: living
Document Class: phase

Status: implemented.

## Objective

Make WSL-side Windows user discovery choose the profile root that is actually
managed by cli-profile-manager.

## Required Behavior

- Keep `USERPROFILE` authoritative when it is set.
- Exclude known system/public profile directories.
- Score candidate users by managed profile markers:
  - `agy-homes`
  - `codex-homes`
  - `claude-homes`
  - `.config/cli-profile-manager`
- Prefer AGY profile contents such as `cred-pN.json` and `pN` directories.
- Fall back deterministically when no candidate has profile markers.

## Implementation Notes

The selection logic must remain side-effect free. It may inspect directory names
and marker presence, but must not create, copy, delete, or mutate profile files.
