# H_02 Phase 02 Incremental Tail Cache

Owner: cli-profile-manager
Source of Truth: management/horizons/H34_Log_Tail_And_Developer_Mode_Optimization/README.md
Lifecycle: living
Document Class: horizon-phase

Status: implemented.

## Objective

Add a small tail cache keyed by file identity and offset.

## Deliverables

- Incremental tail reader.
- Rotation/truncation detection.
- Pre-filtered diagnostic lines.
- Tests for missing and growing log files.

## Result

`live_log_lines` maintains a bounded cache of pre-filtered diagnostic lines,
updates from the previous byte offset when the log grows, and rebuilds the tail
when the file is missing, truncated, or rotated.
