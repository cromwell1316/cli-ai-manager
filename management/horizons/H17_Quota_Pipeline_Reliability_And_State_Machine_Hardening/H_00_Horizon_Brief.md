# H_00 Horizon Brief

Owner: cli-profile-manager
Source of Truth: management/horizons/H17_Quota_Pipeline_Reliability_And_State_Machine_Hardening/README.md
Lifecycle: living
Document Class: brief

Status: completed.

## Context

Quota loading uses background workers, cache states, retry windows, stale value
reuse, PTY subprocesses, and persistent sessions. It directly affects perceived
responsiveness of status screens.

## Problem

The quota pipeline has many implicit state combinations. Without a strict state
machine and deterministic tests, races or unusual native CLI failures can create
confusing UI output, repeated retries, stale data, or stuck sessions.

## Strategy

Define the state machine first, then migrate cache entries, worker behavior, PTY
session lifecycle, diagnostics, and audit events onto that model.
