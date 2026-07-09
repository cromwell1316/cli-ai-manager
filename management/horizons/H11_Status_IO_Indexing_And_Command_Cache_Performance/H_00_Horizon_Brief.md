# H_00 Horizon Brief

Owner: cli-profile-manager
Source of Truth: management/horizons/H11_Status_IO_Indexing_And_Command_Cache_Performance/README.md
Lifecycle: living
Document Class: brief

Status: implemented.

## Context

H09 reduced interactive redraw work by allowing rendered status screens to reuse
collected base statuses. H10 will separate startup/import overhead from command
execution. H11 focuses on the command execution part: unnecessary filesystem
walks, repeated metadata loads, and repeated account lookup work.

## Problem

When a command needs profile status, metadata, labels, diagnostics, and account
data, it is easy for separate functions to rediscover the same files. This
creates avoidable latency and makes performance harder to reason about.

## Strategy

Make command-scoped snapshots explicit, measure filesystem operations in tests,
and add indexes only where invalidation can be proven.
