# H_00 Horizon Brief

Owner: cli-profile-manager
Source of Truth: management/horizons/H38_Fast_Diagnostics_Health_Split/README.md
Lifecycle: living
Document Class: brief

Status: completed.

## Context

Fast diagnostics is intended for quick operational checks, but profiling showed
that it can still enter live configuration health checks.

## Problem

The fast path pays for backend capability probing that belongs to deep
diagnostics. That makes diagnostics slower and less predictable in the runtime
service.

## Strategy

Separate payload construction by diagnostics mode. Fast mode should use only
static effective configuration data, while deep mode keeps live health checks.

## Expected Result

Fast diagnostics avoids process backend probes, and deep diagnostics continues
to report the full health payload.

## Completion Notes

Fast diagnostics now uses static effective configuration health while deep
diagnostics continues to call the live health payload.
