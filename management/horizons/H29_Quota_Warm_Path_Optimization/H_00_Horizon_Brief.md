# H_00 Horizon Brief

Owner: cli-profile-manager
Source of Truth: management/horizons/H29_Quota_Warm_Path_Optimization/README.md
Lifecycle: living
Document Class: brief

Status: planned.

## Context

AGY quota correctness now depends on tmux-backed sessions.

## Problem

Warm quota refreshes can still waste time on fixed sleeps, repeated liveness
checks, and large captures.

## Strategy

Measure cold and warm quota separately, then optimize only the warm path while
preserving recovery semantics.
