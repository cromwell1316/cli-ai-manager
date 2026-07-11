# V_01 Acceptance Matrix

Owner: cli-profile-manager
Source of Truth: management/horizons/H32_Sync_Manifest_And_Copy_Optimization/README.md
Lifecycle: living
Document Class: validation

Status: implemented.

| Area | Acceptance | Evidence |
| --- | --- | --- |
| Correctness | Sync decisions remain equivalent | Existing sync tests plus manifest diff tests |
| Safety | Hard delete preflight remains strict | Hard mode still requires `--yes` outside dry-run and deletes only managed manifest extras |
| Performance | Dry-run and planning do less filesystem traversal | Managed root manifest test fails on `os.walk` |
| Conversion | AGY credential conversion behavior is preserved | Existing AGY conversion sync tests remain passing |
