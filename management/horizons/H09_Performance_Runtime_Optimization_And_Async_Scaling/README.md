# H09 Performance Runtime Optimization And Async Scaling

Owner: cli-profile-manager
Source of Truth: management/horizons/H09_Performance_Runtime_Optimization_And_Async_Scaling/README.md
Lifecycle: living
Document Class: horizon

Status: implemented.

## Purpose

Run a full performance and runtime audit, then optimize the application so
interactive quota/status workflows stay responsive as profile counts, quota
probes, and live validation usage grow.

## Goals

- Establish repeatable performance baselines and budgets for startup, listing,
  status rendering, quota probing, refresh loops, and live validation.
- Reduce synchronous filesystem and log scanning on hot UI paths.
- Make async quota scheduling explicit, deduplicated, observable, and bounded.
- Reduce PTY/session latency and unnecessary process churn without sacrificing
  recovery behavior.
- Split monolithic runtime surfaces into testable components with stable
  contracts.
- Add performance regression tests that can run locally without real CLI tokens.

## Non-Goals

- Do not remove current command names, JSON fields, profile paths, or shortcut
  behavior.
- Do not upload telemetry or add an external service.
- Do not make live quota probes less safe in order to make them faster.
- Do not hide stale quota values when refreshes fail.

## Files

- `H_00_Horizon_Brief.md`
- `H_01_Phase_01_Audit_Baseline_And_Budgets.md`
- `H_02_Phase_02_Async_Scheduler_And_Backpressure.md`
- `H_03_Phase_03_Profile_Status_IO_Caching.md`
- `H_04_Phase_04_PTY_Session_And_Quota_Pipeline.md`
- `H_05_Phase_05_Render_Loop_And_UI_Responsiveness.md`
- `H_06_Phase_06_Modularization_And_Test_Harness.md`
- `H_07_Governance_And_Safety_Boundaries.md`
- `V_00_Validation_Plan.md`
- `V_01_Baseline_Verification.md`
- `V_02_Async_Scheduler_Verification.md`
- `V_03_IO_Caching_Verification.md`
- `V_04_PTY_Pipeline_Verification.md`
- `V_05_UI_Responsiveness_Verification.md`
- `V_06_Modularization_Verification.md`
- `V_07_Acceptance_Matrix.md`
