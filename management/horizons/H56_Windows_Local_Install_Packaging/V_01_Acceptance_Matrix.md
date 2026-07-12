# H56 Acceptance Matrix

Owner: cli-profile-manager
Source of Truth: management/horizons/H56_Windows_Local_Install_Packaging/README.md
Lifecycle: living
Document Class: validation

Status: completed.

| Area | Acceptance |
| --- | --- |
| Local layout | Installed Windows files live outside WSL-dependent paths. |
| Shims | `ai-man`, `profile-man`, and `pman` survive source repo moves. |
| Updates | Reinstall updates the local package predictably. |
| Rollback | Uninstall/rollback removes generated files without deleting profiles. |
| Dev mode | UNC/current checkout shims require explicit `-DevSource`. |
| Verification | Windows smoke validates temporary local app/bin install paths. |
