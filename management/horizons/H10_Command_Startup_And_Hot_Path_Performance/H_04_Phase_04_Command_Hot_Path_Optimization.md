# H_04 Phase 04 Command Hot Path Optimization

Owner: cli-profile-manager
Source of Truth: management/horizons/H10_Command_Startup_And_Hot_Path_Performance/README.md
Lifecycle: living
Document Class: implementation phase

Status: planned.

## Objective

Optimize measured command handlers after startup/import and in-process command
costs are visible.

## Scope

- Fix only hot paths proven by H10 benchmark data.
- Avoid repeated metadata/profile-root scans within one command execution.
- Reuse existing status helpers when they are already IO-efficient.
- Keep JSON output stable and sorted only where already expected.
- Document any remaining bottleneck that belongs to H11 or H12.

## Acceptance

- In-process command benchmarks improve or remain within budget.
- No command starts a quota PTY unless the user requested quota probing.
- `list`, `status`, `diagnostics`, and `config show` keep existing behavior.
