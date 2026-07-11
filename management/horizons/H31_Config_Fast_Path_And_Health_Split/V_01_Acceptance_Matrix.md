# V_01 Acceptance Matrix

Owner: cli-profile-manager
Source of Truth: management/horizons/H31_Config_Fast_Path_And_Health_Split/README.md
Lifecycle: living
Document Class: validation

Status: implemented.

| Area | Acceptance |
| --- | --- |
| Speed | `config show --json` is faster |
| Purity | Effective config avoids live runtime checks |
| Warnings | Invalid env warnings remain correct |
| Compatibility | Existing consumers have a migration path if fields move |

## Result

| Area | Result |
| --- | --- |
| Speed | `config-json` median improved from `129.546ms` to `93.310ms` in the validation run |
| Purity | `config show` avoids live process backend checks and reports deferred backends |
| Warnings | Invalid env warnings remain in `config show` and `config health` |
| Compatibility | Existing `process_limits` field remains; live backend details moved to `config health` |
