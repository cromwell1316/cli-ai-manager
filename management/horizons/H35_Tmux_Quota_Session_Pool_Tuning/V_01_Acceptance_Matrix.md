# V_01 Acceptance Matrix

Owner: cli-profile-manager
Source of Truth: management/horizons/H35_Tmux_Quota_Session_Pool_Tuning/README.md
Lifecycle: living
Document Class: validation

Status: implemented.

| Area | Acceptance |
| --- | --- |
| Bounds | Session creation and warm snapshots have separate bounded concurrency controls |
| Cleanup | Manager-owned sessions are cleaned precisely and close/evict timing is reported |
| Recovery | Dead sessions are invalidated and recreated through the existing recovery path |
| Safety | User tmux sessions are never killed by quota cleanup |
| Diagnostics | Pool status reports backend counts, starting sessions, ready sessions, and lifecycle metrics |
