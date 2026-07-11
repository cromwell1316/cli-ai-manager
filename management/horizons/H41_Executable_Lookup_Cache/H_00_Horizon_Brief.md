# H_00 Horizon Brief

Owner: cli-profile-manager
Source of Truth: management/horizons/H41_Executable_Lookup_Cache/README.md
Lifecycle: living
Document Class: brief

Status: completed.

## Context

Several hot paths need to locate external executables before launching or
checking runtime backends.

## Problem

Repeated `PATH` scans for the same executable add avoidable latency in long-lived
processes and warm quota paths.

## Strategy

Centralize executable discovery behind a process-local cache keyed by command
and `PATH`.

## Expected Result

Repeated lookups avoid duplicate filesystem scans while launch behavior and
missing-executable handling remain unchanged.

## Result

Executable discovery is centralized in a process-local cache keyed by command
and `PATH`. The selected hot paths now use the helper for repeated ordinary
command-name lookups, while explicit executable paths continue to use direct
`shutil.which` resolution. Tests cover cache hits, missing results, `PATH`
invalidation, and explicit-path bypass behavior.
