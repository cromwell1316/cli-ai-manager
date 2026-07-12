# H_01 Phase 01 Backend Boundary And Command Model

Owner: cli-profile-manager
Source of Truth: management/horizons/H45_Windows_AGY_Quota_Backend/README.md
Lifecycle: living
Document Class: horizon-phase

Status: completed.

## Objective

Define the native Windows AGY quota execution boundary.

## Deliverables

- Inventory current quota call sites and PTY assumptions.
- Decide helper action shape for quota probing.
- Define command, environment, timeout, and cwd handling.
- Preserve the existing quota JSON payload contract.

## Validation Focus

- Command construction is deterministic.
- Windows path does not import Unix PTY-only modules.
- WSL/Linux quota behavior remains unchanged.

## Result

The backend boundary is explicit: `operations.quota_probe_runner()` selects the
Windows helper runner only for native Windows AGY. The Windows command model is
`["agy", "-p", "review this code in one sentence"]`; WSL/Linux continues to
pass `["agy"]` into the existing persistent quota runner.
