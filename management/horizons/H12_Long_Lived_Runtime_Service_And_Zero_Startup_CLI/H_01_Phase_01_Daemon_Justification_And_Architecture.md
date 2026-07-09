# H_01 Phase 01 Daemon Justification And Architecture

Owner: cli-profile-manager
Source of Truth: management/horizons/H12_Long_Lived_Runtime_Service_And_Zero_Startup_CLI/README.md
Lifecycle: living
Document Class: implementation phase

Status: planned.

## Objective

Decide whether a long-lived runtime is justified and define its architecture.

## Scope

- Use H10/H11 evidence to compare one-shot and in-process command costs.
- Define which commands are eligible for service execution.
- Keep mutation-heavy flows conservative until invalidation is proven.
- Define service ownership, socket path, log path, pid file, and stale cleanup.
- Define compatibility behavior when the service is absent or unhealthy.

## Acceptance

- The horizon records a go/no-go decision based on measured startup overhead.
- Architecture avoids network exposure and privileged installation.
