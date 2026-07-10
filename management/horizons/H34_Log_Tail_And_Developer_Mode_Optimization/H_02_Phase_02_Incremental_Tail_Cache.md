# H_02 Phase 02 Incremental Tail Cache

Owner: cli-profile-manager
Source of Truth: management/horizons/H34_Log_Tail_And_Developer_Mode_Optimization/README.md
Lifecycle: living
Document Class: horizon-phase

Status: planned.

## Objective

Add a small tail cache keyed by file identity and offset.

## Deliverables

- Incremental tail reader.
- Rotation/truncation detection.
- Pre-filtered diagnostic lines.
- Tests for missing and growing log files.
