# H50 Acceptance Matrix

Owner: cli-profile-manager
Source of Truth: management/horizons/H50_Native_Windows_CI_Smoke_Matrix/README.md
Lifecycle: living
Document Class: validation

Status: completed.

| Area | Acceptance |
|------|------------|
| CI | A native Windows job runs on pull requests. |
| Installer | Windows installer smoke passes in temporary directories. |
| Tokens | CI does not require or expose real account tokens. |
| Regression | Unix-only import regressions are caught. |

## Result

Accepted through `.github/workflows/windows-smoke.yml` and
`scripts/windows_ci_smoke.ps1`, with static tests covering the workflow contract
and token-safe installer verification flags.
