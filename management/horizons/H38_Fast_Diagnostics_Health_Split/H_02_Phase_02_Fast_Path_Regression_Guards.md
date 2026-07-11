# H_02 Phase 02 Fast Path Regression Guards

Owner: cli-profile-manager
Source of Truth: management/horizons/H38_Fast_Diagnostics_Health_Split/README.md
Lifecycle: living
Document Class: horizon-phase

Status: planned.

## Objective

Add focused tests and measurements that keep fast diagnostics from regressing
back into live health collection.

## Deliverables

- Unit coverage proving fast diagnostics does not call backend probes.
- Unit coverage proving deep diagnostics still includes health data.
- Benchmark evidence for diagnostics command execution.
- Notes for any intentionally unchanged slow paths.

## Implementation Notes

- Prefer monkeypatch-based call guards for expensive health helpers.
- Keep benchmark checks informational unless budget guardrails already exist.
