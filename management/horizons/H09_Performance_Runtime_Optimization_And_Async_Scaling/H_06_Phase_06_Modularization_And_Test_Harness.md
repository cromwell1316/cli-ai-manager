# H_06 Phase 06 Modularization And Test Harness

Owner: cli-profile-manager
Source of Truth: management/horizons/H09_Performance_Runtime_Optimization_And_Async_Scaling/README.md
Lifecycle: living
Document Class: implementation phase

Status: implemented.

## Objective

Make the optimized runtime maintainable by splitting large modules and adding
targeted performance tests.

## Scope

- Split `interactive.py` into focused modules for key input, rendering, quota
  runtime, and profile actions.
- Split `quota.py` into parser, PTY session, persistent session registry, and
  payload modules.
- Keep `profile_manager.py` and direct command imports backward compatible.
- Add fake-clock, fake-filesystem, fake-terminal, and fake-PTY helpers.
- Keep behavior tests close to the module they verify where practical.

## Acceptance

- Module boundaries reduce cross-import cycles.
- Existing command and import compatibility tests pass.
- Performance tests are deterministic and do not require real CLI binaries.
- The test suite remains fast enough for routine local execution.
