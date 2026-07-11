# V_01 Acceptance Matrix

Owner: cli-profile-manager
Source of Truth: management/horizons/H38_Fast_Diagnostics_Health_Split/README.md
Lifecycle: living
Document Class: validation

Status: planned.

| Area | Acceptance | Evidence |
| --- | --- | --- |
| Fast path | Fast diagnostics does not run live process backend checks | Unit test with backend probe guard |
| Deep path | Deep diagnostics still reports full health data | Deep diagnostics JSON test |
| Compatibility | Existing diagnostics command shape remains stable | Targeted diagnostics tests |
| Performance | Diagnostics benchmark improves or does not regress | Runtime benchmark output |
