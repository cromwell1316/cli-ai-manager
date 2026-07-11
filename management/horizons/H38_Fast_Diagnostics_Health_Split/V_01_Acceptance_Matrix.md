# V_01 Acceptance Matrix

Owner: cli-profile-manager
Source of Truth: management/horizons/H38_Fast_Diagnostics_Health_Split/README.md
Lifecycle: living
Document Class: validation

Status: completed.

| Area | Acceptance | Evidence |
| --- | --- | --- |
| Fast path | Fast diagnostics does not run live process backend checks | `test_fast_diagnostics_does_not_resolve_live_process_backend` |
| Deep path | Deep diagnostics still reports full health data | `test_deep_diagnostics_keeps_live_config_health` |
| Compatibility | Existing diagnostics command shape remains stable | `pytest -q tests/test_profile_manager.py -k diagnostics` |
| Performance | Diagnostics benchmark remains measured under guardrails | `command-diagnostics-agy-json` median 65.947ms |
