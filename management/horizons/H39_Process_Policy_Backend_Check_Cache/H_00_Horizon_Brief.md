# H_00 Horizon Brief

Owner: cli-profile-manager
Source of Truth: management/horizons/H39_Process_Policy_Backend_Check_Cache/README.md
Lifecycle: living
Document Class: brief

Status: completed.

## Context

Process backend selection can invoke system capability checks, including
systemd user-scope probing.

## Problem

Repeated checks in the same process redo identical work and dominate some
config and diagnostics profiles.

## Strategy

Cache capability results per process with an environment-sensitive key and a
test reset hook.

## Expected Result

Repeated process policy calls avoid duplicate system probes without changing
backend selection semantics.
