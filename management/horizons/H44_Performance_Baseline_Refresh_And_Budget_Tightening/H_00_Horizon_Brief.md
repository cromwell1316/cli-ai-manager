# H_00 Horizon Brief

Owner: cli-profile-manager
Source of Truth: management/horizons/H44_Performance_Baseline_Refresh_And_Budget_Tightening/README.md
Lifecycle: living
Document Class: brief

Status: planned.

## Context

After optimization work lands, benchmark guardrails need to represent the new
steady state.

## Problem

Old performance budgets may be too loose to catch regressions, while overly
tight budgets can create noise.

## Strategy

Capture fresh baselines with enough iterations, then tighten only stable budgets
with clear headroom.

## Expected Result

Performance guardrails become stricter where evidence supports it and remain
practical for normal development runs.
