# V_01 Acceptance Matrix

Owner: cli-profile-manager
Source of Truth: management/horizons/H35_Tmux_Quota_Session_Pool_Tuning/README.md
Lifecycle: living
Document Class: validation

Status: planned.

| Area | Acceptance |
| --- | --- |
| Bounds | Session count remains bounded |
| Cleanup | Manager-owned sessions are cleaned precisely |
| Recovery | Dead sessions are recreated cleanly |
| Safety | User tmux sessions are never killed |
