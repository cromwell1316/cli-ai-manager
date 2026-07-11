# V_01 Acceptance Matrix

Owner: cli-profile-manager
Source of Truth: management/horizons/H29_Quota_Warm_Path_Optimization/README.md
Lifecycle: living
Document Class: validation

Status: implemented.

| Area | Acceptance |
| --- | --- |
| Warm latency | Warm AGY quota refresh is faster |
| Reliability | No increase in parser misses or false auth failures |
| Recovery | Dead sessions still recover |
| Compatibility | Quota payload shape is unchanged |

## Result

| Area | Result |
| --- | --- |
| Warm latency | Fixed sleep is replaced by marker-driven short-capture polling |
| Reliability | Parser miss fallback captures a wider pane before returning |
| Recovery | Dead tmux sessions raise `process_exit` and remain invalidating |
| Compatibility | Quota payload shape remains unchanged; metrics live on session diagnostics |
