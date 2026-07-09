# H_07 Governance And Safety Boundaries

Owner: cli-profile-manager
Source of Truth: management/horizons/H09_Performance_Runtime_Optimization_And_Async_Scaling/README.md
Lifecycle: living
Document Class: governance

Status: implemented.

## Boundaries

- Optimization must be measured. Do not merge speculative speed changes without
  before/after evidence or deterministic tests.
- Preserve stale quota values when refreshes fail.
- Do not increase token exposure risk in logs, diagnostics, benchmarks, or test
  fixtures.
- Do not make default concurrency aggressive enough to overload local machines
  or native CLI auth/session systems.
- Do not break JSON contracts, command names, profile directories, labels, or
  current keyboard shortcuts.
- Refactors must be incremental and keep the working tree testable after each
  phase.
- Live AGY validation is optional evidence and must remain sanitized.
