# H_00 Horizon Brief

Owner: cli-profile-manager
Source of Truth: management/horizons/H33_Benchmark_Budgets_And_Regression_Guardrails/README.md
Lifecycle: living
Document Class: brief

Status: implemented.

## Context

Performance work needs stable evidence, not only manual timings.

## Problem

Single wall-clock tests can be noisy and do not explain which section regressed.

## Strategy

Make benchmarks structured, sectioned, and comparable while keeping live-token
requirements out of normal tests.

## Outcome

Benchmarks now produce schema-versioned JSON, can be compared with a stored
local baseline, and report named regression sections with tolerances instead of
depending only on ad hoc wall-clock readings.
