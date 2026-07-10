# V_01 Acceptance Matrix

Owner: cli-profile-manager
Source of Truth: management/horizons/H27_Runtime_Service_Acceleration/README.md
Lifecycle: living
Document Class: validation

Status: planned.

| Area | Acceptance |
| --- | --- |
| Speed | Service-backed read-only commands are faster than one-shot |
| Correctness | Outputs match one-shot behavior |
| Invalidation | Mutating commands invalidate relevant state |
| Fallback | One-shot path remains reliable |
