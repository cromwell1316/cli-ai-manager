# H_00 Horizon Brief

Owner: cli-profile-manager
Source of Truth: management/horizons/H25_Diagnostics_Fast_Path/README.md
Lifecycle: living
Document Class: brief

Status: implemented.

## Context

`diagnostics` is currently the slowest read-only command because it gathers
many independent runtime sections in one pass.

## Problem

Users need fast operational visibility most of the time, while deep diagnostics
are only needed during troubleshooting.

## Strategy

Split diagnostics collection into measured sections, introduce a fast path, and
cache expensive local probes without changing safe redaction behavior.
