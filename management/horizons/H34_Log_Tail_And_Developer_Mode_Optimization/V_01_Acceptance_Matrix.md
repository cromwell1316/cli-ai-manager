# V_01 Acceptance Matrix

Owner: cli-profile-manager
Source of Truth: management/horizons/H34_Log_Tail_And_Developer_Mode_Optimization/README.md
Lifecycle: living
Document Class: validation

Status: planned.

| Area | Acceptance |
| --- | --- |
| Cost | Developer mode does not materially slow redraw |
| Correctness | New relevant log lines appear |
| Robustness | Missing, rotated, and truncated logs are handled |
| Safety | Token-like values remain redacted upstream |
