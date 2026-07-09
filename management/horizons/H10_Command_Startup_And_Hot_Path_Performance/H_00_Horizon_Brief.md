# H_00 Horizon Brief

Owner: cli-profile-manager
Source of Truth: management/horizons/H10_Command_Startup_And_Hot_Path_Performance/README.md
Lifecycle: living
Document Class: brief

Status: planned.

## Context

H09 added runtime benchmarks and showed that parser and redraw paths are fast,
while subprocess command benchmarks can be dominated by the host Python startup
cost. In the observed environment, even `python3 -c 'print(1)'` was much slower
than any in-process command work. H10 must therefore measure phases separately
before changing code.

## Problem

The current CLI path can only report end-to-end subprocess duration. That hides
whether latency comes from:

- Python executable startup.
- Importing `profile_manager.py` and package modules.
- Building the argparse tree.
- Command handler logic.
- Filesystem traversal performed by the command itself.

Without this split, optimization work can chase the wrong bottleneck.

## Strategy

Build a measurement harness that exposes each phase, use import profiling to
find avoidable top-level imports, then make command handlers lazy and testable
in-process. Only optimize command-specific IO once the startup/import baseline
is clear.
