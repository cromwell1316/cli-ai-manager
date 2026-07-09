# H_04 Phase 04 Install Update And Compatibility Sweep

Owner: cli-profile-manager
Source of Truth: management/horizons/H22_End_To_End_Operational_Reliability_Sweep/README.md
Lifecycle: living
Document Class: implementation phase

Status: implemented.

## Objective

Verify installation, update, and platform compatibility after all changes.

## Scope

- Run install and verification scripts.
- Verify metadata migration from older versions.
- Verify Linux and WSL paths.
- Verify optional dependencies are not accidentally required.
- Verify README install instructions match behavior.

## Acceptance

- Install verification passes.
- Existing metadata remains readable.
- WSL and Linux compatibility evidence is recorded.

## Evidence

Install verification:

```bash
./scripts/verify_install.sh
```

Result:

```text
install verification passed: aliases point at /home/olivercromwell/projects/shared/cli-profile-manager/profile_manager.py
```

Compatibility smoke checks ran with temporary `AI_MAN_*` roots for Linux/WSL
path behavior. Diagnostics, audit status, service status, and profile workflows
completed without using real user profile data.
