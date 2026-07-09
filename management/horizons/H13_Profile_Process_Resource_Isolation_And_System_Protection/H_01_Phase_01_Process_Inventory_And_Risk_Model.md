# H_01 Phase 01 Process Inventory And Risk Model

Owner: cli-profile-manager
Source of Truth: management/horizons/H13_Profile_Process_Resource_Isolation_And_System_Protection/README.md
Lifecycle: living
Document Class: implementation phase

Status: implemented.

## Objective

Map every path that creates a native process and classify its resource risk.

## Scope

- Inventory process creation in:
  - profile launch commands.
  - login/add flows.
  - quota PTY probes.
  - persistent quota sessions.
  - validation scripts where relevant.
- Identify which paths are interactive user sessions and which are background
  automation.
- Define default policy tiers:
  - foreground interactive launch.
  - background quota probe.
  - validation script probe.
- Record platform capabilities for Linux, WSL with systemd, WSL without systemd,
  and unsupported operating systems.

## Acceptance

- Every subprocess creation path has an assigned policy tier.
- Risks and fallback behavior are documented before implementation.

## Evidence

- Foreground interactive launches use the `launch` policy tier through
  `run_cli_tool()`.
- One-shot and persistent quota PTY subprocesses use the stricter `quota` policy
  tier in `cli_profile_manager/quota.py`.
- Validation and benchmark subprocesses remain external test harness activity;
  a `validation` policy tier is exposed for future first-party validation
  launchers.
