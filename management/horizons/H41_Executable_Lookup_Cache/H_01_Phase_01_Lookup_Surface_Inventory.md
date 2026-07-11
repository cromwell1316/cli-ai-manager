# H_01 Phase 01 Lookup Surface Inventory

Owner: cli-profile-manager
Source of Truth: management/horizons/H41_Executable_Lookup_Cache/README.md
Lifecycle: living
Document Class: horizon-phase

Status: completed.

## Objective

Identify executable lookup sites worth caching.

## Deliverables

- Inventory of `shutil.which` and equivalent lookup calls.
- Hot-path classification for each lookup.
- Cache eligibility decision for each site.
- Risk notes for explicit executable paths.

## Implementation Notes

- Cache only lookups that depend on command name and `PATH`.
- Leave one-off or already-cheap lookup sites unchanged unless evidence says
  otherwise.

## Inventory

| Site | Lookup | Hot-path classification | Decision |
| --- | --- | --- | --- |
| `cli_profile_manager.diagnostics.tool_diagnostics` | tool CLI availability | diagnostics fast path | Cache ordinary command lookups |
| `cli_profile_manager.process_policy._systemd_user_scope_available_uncached` | `systemd-run` | launch backend probe | Cache ordinary command lookup |
| `cli_profile_manager.process_policy.ionice_command` | `ionice` | launch/quota process wrapping | Cache ordinary command lookup |
| `cli_profile_manager.quota.tmux_path` | `tmux` | quota backend selection and tmux commands | Cache ordinary command lookup |
| `cli_profile_manager.quota.start_quota_pty_process` | target CLI | quota cold startup | Cache ordinary command lookup |
| `cli_profile_manager.quota.TmuxQuotaSession.start` | target CLI | tmux quota cold startup | Cache ordinary command lookup |
| `cli_profile_manager.quota.run_direct_cli_prompt_snapshot` | target CLI | direct quota prompt startup | Cache ordinary command lookup |
| `cli_profile_manager.cli.run_cli_tool` | tool CLI | command launch guard | Cache ordinary command lookup |
| Windows PowerShell launch branch | `powershell.exe` / `powershell` | Windows-only launch branch | Left unchanged as a platform-specific fallback |

## Risk Notes

- Explicit executable paths are not cached, avoiding stale behavior for direct
  path invocations.
- Cache entries are process-local only and never persisted.
- `None` is cached intentionally so repeated missing executable checks do not
  rescan the same `PATH`.
