# V_01 Acceptance Matrix

Owner: cli-profile-manager
Source of Truth: management/horizons/H34_Log_Tail_And_Developer_Mode_Optimization/README.md
Lifecycle: living
Document Class: validation

Status: implemented.

| Area | Acceptance | Evidence |
| --- | --- | --- |
| Cost | Developer mode does not materially slow redraw | `status-redraw` median `0.009ms` |
| Correctness | New relevant log lines appear | Incremental growth test |
| Robustness | Missing, rotated, and truncated logs are handled | Tail cache reset tests |
| Safety | Token-like values remain redacted upstream | Existing redaction tests remain passing |
