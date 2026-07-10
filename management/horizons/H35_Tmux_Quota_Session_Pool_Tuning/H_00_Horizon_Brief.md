# H_00 Horizon Brief

Owner: cli-profile-manager
Source of Truth: management/horizons/H35_Tmux_Quota_Session_Pool_Tuning/README.md
Lifecycle: living
Document Class: brief

Status: planned.

## Context

AGY quota now uses tmux sessions for terminal parity.

## Problem

Multi-profile quota refreshes need bounded startup, reuse, and cleanup so they
do not waste process resources.

## Strategy

Tune tmux session pooling, ownership, concurrency, and eviction with live and
fake-session validation.
