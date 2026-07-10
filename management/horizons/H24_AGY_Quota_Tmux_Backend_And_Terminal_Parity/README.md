# H24 AGY Quota Tmux Backend And Terminal Parity

Owner: cli-profile-manager
Source of Truth: management/horizons/H24_AGY_Quota_Tmux_Backend_And_Terminal_Parity/README.md
Lifecycle: living
Document Class: horizon

Status: implemented.

## Purpose

Make AGY quota refresh behave like a real terminal launch. AGY CLI 1.1.1 does
not reliably complete startup inside the current bare Python PTY quota backend:
it emits terminal capability queries, remains in a sign-in bootstrap state, and
prevents `/usage` from being sent. A tmux-backed AGY quota session reaches the
normal prompt with the same `HOME` and `cwd`, and `/usage` returns quota output.

## Goals

- Add a tmux quota backend for AGY profiles.
- Preserve profile isolation through per-profile `HOME`.
- Preserve terminal parity with manual `agyN` launches.
- Keep the existing Python PTY backend as fallback.
- Keep Codex and Claude quota behavior unchanged.
- Treat AGY eligibility as a warning, not a fatal quota state.
- Avoid false `auth_required` states while AGY is still bootstrapping.
- Manage tmux session lifecycle, cleanup, TTL, and eviction safely.
- Add deterministic tests around backend selection, command dispatch, parsing,
  cleanup, and fallback.

## Non-Goals

- Do not replace all quota probing with tmux.
- Do not require tmux for Codex or Claude.
- Do not infer or modify user credentials.
- Do not kill unrelated user tmux sessions.
- Do not hide real authentication failures when AGY explicitly asks for login.
- Do not make one-shot AGY quota probing the primary path again.

## Diagnostic Facts

- Manual `agy1` sets `HOME=/home/olivercromwell/agy-homes/p1` and executes
  `/home/olivercromwell/.local/bin/agy`.
- Manual `agy1` does not change `cwd`.
- Current AGY quota now uses `cwd=/home/olivercromwell` and profile `HOME`.
- Disabling quota process limits did not fix the bare PTY sign-in stall.
- A bare `script` session also failed to reach a useful prompt in the observed
  window.
- A tmux session with the same `HOME` and `cwd` reached the AGY prompt.
- `/usage` sent through tmux returned the models and quota screen.

## Files

- `H_00_Horizon_Brief.md`
- `H_01_Phase_01_Backend_Selection_And_Config_Surface.md`
- `H_02_Phase_02_Tmux_Session_Model.md`
- `H_03_Phase_03_Readiness_And_State_Mapping.md`
- `H_04_Phase_04_Command_Dispatch_And_Quota_Capture.md`
- `H_05_Phase_05_Lifecycle_Cleanup_And_Eviction.md`
- `H_06_Phase_06_Fallback_And_Compatibility.md`
- `H_07_Governance_And_Safety_Boundaries.md`
- `V_00_Validation_Plan.md`
- `V_01_Backend_Selection_Verification.md`
- `V_02_Tmux_Session_Verification.md`
- `V_03_Readiness_State_Verification.md`
- `V_04_Lifecycle_And_Cleanup_Verification.md`
- `V_05_Live_AGY_Verification.md`
- `V_06_Acceptance_Matrix.md`
