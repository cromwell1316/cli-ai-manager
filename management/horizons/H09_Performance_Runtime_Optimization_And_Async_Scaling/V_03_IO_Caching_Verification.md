# V_03 IO Caching Verification

Owner: cli-profile-manager
Source of Truth: management/horizons/H09_Performance_Runtime_Optimization_And_Async_Scaling/README.md
Lifecycle: living
Document Class: validation

Status: implemented.

## Checks

- Status redraws do not call profile discovery, metadata loading, or AGY log
  scanning after the initial snapshot.
- Cache invalidates on login, import, export, label, clear, and sync.
- Diagnostics can bypass cache or clearly label cached data.
- Direct command JSON contracts remain stable.

## Evidence

- Interactive status rendering can reuse an already collected base status
  snapshot, so quota redraws do not repeat profile discovery or account IO.
- `collect_status_snapshot` separates profile status collection from quota merge
  and terminal rendering.
- `status_with_auto_quota_snapshot` lets tests and redraw loops merge quota
  state without re-reading profile roots.
- The regression suite covers status collection not waiting for quota workers
  and direct command JSON compatibility.
