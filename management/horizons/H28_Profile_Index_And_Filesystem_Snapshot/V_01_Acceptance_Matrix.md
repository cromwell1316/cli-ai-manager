# V_01 Acceptance Matrix

Owner: cli-profile-manager
Source of Truth: management/horizons/H28_Profile_Index_And_Filesystem_Snapshot/README.md
Lifecycle: living
Document Class: validation

Status: implemented.

| Area | Acceptance | Evidence |
| --- | --- | --- |
| IO | Repeated list/status filesystem work is reduced | `ProfileIndex` reuses discovery and file facts inside `CommandSnapshot` |
| Safety | Raw credential contents are not cached | Index stores paths, existence, mtime, and size only |
| Correctness | Profile changes are reflected on the next command | Runtime service stale-fingerprint invalidation test |
| Reuse | Diagnostics and status can share indexed facts | Diagnostics profile index provider and snapshot tests |
