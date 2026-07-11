# H_01 Phase 01 Cache Key And Reset Contract

Owner: cli-profile-manager
Source of Truth: management/horizons/H39_Process_Policy_Backend_Check_Cache/README.md
Lifecycle: living
Document Class: horizon-phase

Status: completed.

## Objective

Define safe cache inputs and the reset contract for tests.

## Deliverables

- Cache key for command, `PATH`, `XDG_RUNTIME_DIR`, and relevant backend inputs.
- Explicit behavior when environment values change.
- Test-only cache reset helper.
- Documentation of cache lifetime as process-local only.

## Implementation Notes

- Do not persist cache entries to disk.
- Prefer small immutable key tuples.
- Keep failures cached only when they are tied to the same key.

## Completion Notes

- Cache lifetime is process-local only.
- `reset_process_policy_cache()` clears cached capability checks for tests.
- Cache key includes OS name, probe command, `PATH`, `XDG_RUNTIME_DIR`, and
  `AI_MAN_PROCESS_SYSTEMD`.
