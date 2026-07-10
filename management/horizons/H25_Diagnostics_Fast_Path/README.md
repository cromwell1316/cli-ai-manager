# H25 Diagnostics Fast Path

Owner: cli-profile-manager
Source of Truth: management/horizons/H25_Diagnostics_Fast_Path/README.md
Lifecycle: living
Document Class: horizon

Status: implemented.

## Purpose

Reduce the latency of `diagnostics` without changing its JSON contract for the
default supported fields. The current diagnostics path is the slowest measured
read-only command because it aggregates environment, process policy, service,
profile, quota, audit, and safety data in one pass.

## Goals

- Split diagnostics into fast and deep collection tiers.
- Cache expensive local checks inside one process or runtime-service session.
- Avoid collecting unrelated sections when a specific tool or narrow view is
  requested.
- Preserve safe redaction behavior for accounts and token-like values.
- Keep full diagnostics available for troubleshooting.

## Non-Goals

- Do not remove existing diagnostics fields without a compatibility plan.
- Do not expose raw tokens or credential contents.
- Do not make diagnostics depend on network access.

## Work Areas

- Measure each diagnostics section independently.
- Introduce section-level collection helpers.
- Cache process policy availability checks such as `systemd-run`.
- Make `diagnostics --json` reuse command snapshots where possible.
- Add a fast/deep mode boundary if the command surface permits it.

## Validation

```bash
python3 scripts/benchmark_runtime.py --scenario commands
pytest -q tests/test_profile_manager.py -k "diagnostics"
```

Acceptance target: reduce subprocess `diagnostics agy --json` latency
materially while preserving output compatibility and redaction.

## Files

- `H_00_Horizon_Brief.md`
- `H_01_Phase_01_Section_Baseline_And_Boundary.md`
- `H_02_Phase_02_Fast_Collector_And_Cached_Probes.md`
- `README.md`
- `V_00_Validation_Plan.md`
- `V_01_Acceptance_Matrix.md`

## Implementation Evidence

- Added fast/deep diagnostics modes.
- CLI `diagnostics` defaults to fast mode.
- CLI `diagnostics --deep` preserves full expensive runtime probes.
- Fast mode skips full audit event scans and live systemd availability checks.
- Programmatic `diagnostics_payload()` remains deep by default for compatibility.
- Benchmark sample after implementation: `diagnostics-agy-json` median around
  `172 ms` over 5 subprocess runs.
