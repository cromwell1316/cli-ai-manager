# H_00 Horizon Brief

Owner: cli-profile-manager
Source of Truth: management/horizons/H40_Cached_Command_Parser_For_Runtime_Service/README.md
Lifecycle: living
Document Class: brief

Status: completed.

## Context

Runtime-service command execution currently benefits from staying in process,
but parser construction still appears in command profiles.

## Problem

Repeatedly building the same argparse tree wastes time for simple read-only
commands.

## Strategy

Keep `build_parser()` as a fresh factory, and add a separate cached parser path
for the long-lived runtime-service execution path.

## Expected Result

Runtime-service commands avoid parser rebuild overhead while public CLI parsing
and tests retain fresh-parser semantics.

## Completion Notes

In-process `run_cli` execution now uses the cached parser accessor by default,
which also covers runtime-service requests. Callers that need a fresh parser can
still call `build_parser()` directly or pass it as `parser_factory`.
