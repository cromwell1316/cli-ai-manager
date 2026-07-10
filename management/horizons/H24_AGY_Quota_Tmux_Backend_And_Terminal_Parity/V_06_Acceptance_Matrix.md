# V_06 Acceptance Matrix

Owner: cli-profile-manager
Source of Truth: management/horizons/H24_AGY_Quota_Tmux_Backend_And_Terminal_Parity/README.md
Lifecycle: living
Document Class: validation

Status: implemented.

## Acceptance Criteria

| Area | Required Result | Evidence |
| --- | --- | --- |
| Backend selection | AGY uses tmux in auto mode when tmux is present | Unit test and log |
| Fallback | AGY can force PTY with env rollback | Unit test |
| Missing tmux | Forced tmux mode fails clearly if tmux is absent | Unit test |
| Non-AGY tools | Codex and Claude remain on current PTY path | Unit test |
| Profile isolation | Per-profile `HOME` is preserved | Unit test and live log |
| Terminal parity | `cwd` matches manual wrapper behavior | Unit test and live log |
| Readiness | Prompt after eligibility warning is ready | Unit test |
| Bootstrap | Transient sign-in text is startup pending | Unit test |
| Command dispatch | `/usage` is sent through tmux send-keys | Unit test |
| Capture | Quota screen is read through capture-pane | Unit test |
| Parsing | Existing AGY parser reads tmux capture output | Unit test |
| Cleanup | Manager-owned tmux sessions are killed on close | Unit test |
| Eviction | TTL and max-count eviction work | Unit test |
| Safety | No broad tmux kill commands | Code review |
| Live p1 | Real AGY p1 returns quota or clear quota-exhausted state | Manual evidence |
| Live p1-p11 | Multi-profile refresh avoids false auth storm | Manual evidence |

## Definition Of Done

- All targeted tests pass.
- Broad quota test subset passes.
- Live p1 tmux-backed quota probe reaches `/usage`.
- Logs identify selected backend and session lifecycle.
- Rollback env variable is documented and verified.
- Working tree contains no unrelated changes.
