# H_00 Horizon Brief

Owner: cli-profile-manager
Source of Truth: management/horizons/H35_Tmux_Quota_Session_Pool_Tuning/README.md
Lifecycle: living
Document Class: brief

Status: implemented.

## Context

AGY quota now uses tmux sessions for terminal parity.

## Problem

Multi-profile quota refreshes need bounded startup, reuse, and cleanup so they
do not waste process resources.

## Strategy

Tune tmux session pooling, ownership, concurrency, and eviction with live and
fake-session validation.

## Result

The tmux quota backend now exposes bounded cold-start and warm-snapshot paths,
reports pool/lifecycle diagnostics, avoids evicting in-flight startup sessions,
and refuses to close tmux sessions outside the manager-owned namespace.
