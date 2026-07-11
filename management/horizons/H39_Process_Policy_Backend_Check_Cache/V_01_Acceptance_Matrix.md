# V_01 Acceptance Matrix

Owner: cli-profile-manager
Source of Truth: management/horizons/H39_Process_Policy_Backend_Check_Cache/README.md
Lifecycle: living
Document Class: validation

Status: completed.

| Area | Acceptance | Evidence |
| --- | --- | --- |
| Cache safety | Identical inputs reuse one backend probe result | Cache hit unit test |
| Invalidation | `PATH` or runtime environment changes produce a miss | Cache key unit test |
| Behavior | Backend fallback semantics remain unchanged | Process policy tests |
| Performance | Repeated config and diagnostics calls get cheaper | Runtime benchmark output |

Completion: all acceptance rows are covered by the implementation and validation
commands listed in `V_00_Validation_Plan.md`.
