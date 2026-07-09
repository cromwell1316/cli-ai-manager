# H_01 Phase 01 Audit Baseline And Budgets

Owner: cli-profile-manager
Source of Truth: management/horizons/H09_Performance_Runtime_Optimization_And_Async_Scaling/README.md
Lifecycle: living
Document Class: implementation phase

Status: implemented.

## Objective

Create repeatable measurements before changing runtime behavior.

## Scope

- Add local benchmark commands or scripts for:
  - `python3 profile_manager.py --help`
  - `python3 profile_manager.py list agy --json`
  - `python3 profile_manager.py diagnostics agy --json`
  - interactive status first paint with fake profiles
  - async redraw loop with fake quota workers
  - quota parser throughput on captured terminal output
- Measure cold and warm runs separately.
- Count filesystem operations on hot paths using monkeypatched test fixtures.
- Count queue submissions and duplicate scheduling behavior.
- Record baselines in H09 validation evidence without storing tokens or raw
  credential contents.

## Initial Budgets

- Non-quota `list <tool> --json`: under 200 ms on a normal local checkout with
  12 visible profiles.
- Interactive status first paint without quota completion: under 150 ms after
  entering the tool screen with profile metadata cached.
- Status redraw while quota probes are active: under 50 ms and zero profile-log
  rescans per redraw.
- One active quota job per `(tool, profile)` at a time.
- Manual refresh should preserve stale quota values and enqueue at most one new
  job per visible active profile.
- Fake parser benchmark: parse 100 captured quota outputs in under 250 ms.

## Acceptance

- Baseline script exists and can run without live tokens.
- Budgets are documented and have test coverage where deterministic.
- Regressions can be detected in CI/local test runs without depending on real
  AGY/Codex/Claude processes.
