# V_01 Acceptance Matrix

Owner: cli-profile-manager
Source of Truth: management/horizons/H43_Config_Show_Payload_Construction_Optimization/README.md
Lifecycle: living
Document Class: validation

Status: completed.

| Area | Acceptance | Evidence |
| --- | --- | --- |
| Schema | `config show --json` fields and values remain stable | `test_effective_config_payload_schema_is_stable` |
| Boundary | Health probes are not added to plain config output | `test_config_show_json_does_not_import_live_process_policy` and fast-path tests |
| Performance | Config command medians improve or do not regress | `command-config-json` 2.031ms, `config-json` 47.122ms |
| Scope | No config semantics change | Config slice plus full pytest suite |
