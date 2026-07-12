# H_03 Phase 03 Local Reproduction And Governance

Owner: cli-profile-manager
Source of Truth: management/horizons/H50_Native_Windows_CI_Smoke_Matrix/README.md
Lifecycle: living
Document Class: horizon-phase

Status: completed.

## Objective

Document local reproduction and governance evidence for Windows CI.

## Deliverables

- README or horizon notes for local Windows smoke commands.
- CI status evidence after workflow lands.
- Governance updates if validation commands change.

## Validation Focus

- Developers can reproduce the CI smoke locally.
- Horizon governance remains clean.

## Completion Evidence

- README documents `.\scripts\windows_ci_smoke.ps1` with temporary `BinDir` and
  `AgyHome` arguments.
- H50 validation commands now include py_compile, focused Windows tests,
  governance, and full pytest.
- Governance reports H50 as implemented with no issues or warnings.
