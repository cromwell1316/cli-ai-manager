# H_00 Horizon Brief

Owner: cli-profile-manager
Source of Truth: management/horizons/H43_Config_Show_Payload_Construction_Optimization/README.md
Lifecycle: living
Document Class: brief

Status: completed.

## Context

`config show --json` is a common read-only command and appears in runtime
benchmarks.

## Problem

Payload construction and serialization can do more work than needed for plain
config output.

## Strategy

Profile the config payload path and remove redundant construction work while
preserving the exact JSON schema.

## Expected Result

Config JSON output remains stable, and command execution time improves in both
in-process and cold subprocess measurements.

## Result

Plain `config show --json` now avoids importing live process policy code and
constructs the config payload with fewer intermediate passes. The live health
boundary remains unchanged for `config health` and deep diagnostics. Schema
regression tests lock the top-level payload keys, setting field keys, source
stripping behavior, and fast-path import boundary.
