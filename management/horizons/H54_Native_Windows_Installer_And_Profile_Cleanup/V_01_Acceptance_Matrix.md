# H54 Acceptance Matrix

Owner: cli-profile-manager
Source of Truth: management/horizons/H54_Native_Windows_Installer_And_Profile_Cleanup/README.md
Lifecycle: living
Document Class: validation

Status: completed.

| Area | Acceptance |
| --- | --- |
| Python detection | Broken launchers are skipped in favor of a working Python 3. |
| Profile cleanup | Stale PowerShell functions are detected and remediated safely. |
| Installer | Re-running install is idempotent and updates shims/helpers. |
| Verification | Failures include actionable repair commands. |
| Rollback | Profile cleanup writes backups and the runbook documents restoration. |
