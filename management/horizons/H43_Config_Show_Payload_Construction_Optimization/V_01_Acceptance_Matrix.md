# V_01 Acceptance Matrix

Owner: cli-profile-manager
Source of Truth: management/horizons/H43_Config_Show_Payload_Construction_Optimization/README.md
Lifecycle: living
Document Class: validation

Status: planned.

| Area | Acceptance | Evidence |
| --- | --- | --- |
| Schema | `config show --json` fields and values remain stable | Payload regression tests |
| Boundary | Health probes are not added to plain config output | Config fast-path tests |
| Performance | Config command medians improve or do not regress | Benchmark output |
| Scope | No config semantics change | Existing config tests |
