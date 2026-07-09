# H_00 Horizon Brief

Owner: cli-profile-manager
Source of Truth: management/horizons/H19_Runtime_Service_Consistency_And_Cache_Invalidation_Guarantees/README.md
Lifecycle: living
Document Class: brief

Status: planned.

## Context

The runtime service can speed up read-only commands by keeping process state
alive. Mutating commands still run one-shot and invalidate service state
best-effort.

## Problem

A second execution mode creates risk of stale results, inconsistent config,
different error behavior, and incomplete invalidation after mutations.

## Strategy

Document runtime state ownership, add explicit invalidation contracts, test
one-shot/service equivalence, and expose runtime health through diagnostics and
audit.
