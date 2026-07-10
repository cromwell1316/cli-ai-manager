# V_01 Acceptance Matrix

Owner: cli-profile-manager
Source of Truth: management/horizons/H31_Config_Fast_Path_And_Health_Split/README.md
Lifecycle: living
Document Class: validation

Status: planned.

| Area | Acceptance |
| --- | --- |
| Speed | `config show --json` is faster |
| Purity | Effective config avoids live runtime checks |
| Warnings | Invalid env warnings remain correct |
| Compatibility | Existing consumers have a migration path if fields move |
