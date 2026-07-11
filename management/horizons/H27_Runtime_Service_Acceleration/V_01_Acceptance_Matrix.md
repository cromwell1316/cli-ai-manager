# V_01 Acceptance Matrix

Owner: cli-profile-manager
Source of Truth: management/horizons/H27_Runtime_Service_Acceleration/README.md
Lifecycle: living
Document Class: validation

Status: implemented.

| Area | Acceptance |
| --- | --- |
| Speed | Service-backed read-only commands are faster than one-shot |
| Correctness | Outputs match one-shot behavior |
| Invalidation | Mutating commands invalidate relevant state |
| Fallback | One-shot path remains reliable |

## Result

| Area | Result |
| --- | --- |
| Speed | Repeated service-backed `config`, `list`, and `status` requests hit an in-process response cache and reuse a command snapshot |
| Correctness | Existing one-shot/service output equivalence tests pass |
| Invalidation | Runtime invalidation clears cache entries and increments generation |
| Fallback | Service absence still falls back to one-shot execution |
