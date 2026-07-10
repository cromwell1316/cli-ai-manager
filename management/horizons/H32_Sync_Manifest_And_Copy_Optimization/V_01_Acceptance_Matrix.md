# V_01 Acceptance Matrix

Owner: cli-profile-manager
Source of Truth: management/horizons/H32_Sync_Manifest_And_Copy_Optimization/README.md
Lifecycle: living
Document Class: validation

Status: planned.

| Area | Acceptance |
| --- | --- |
| Correctness | Sync decisions remain equivalent |
| Safety | Hard delete preflight remains strict |
| Performance | Dry-run and planning do less filesystem traversal |
| Conversion | AGY credential conversion behavior is preserved |
