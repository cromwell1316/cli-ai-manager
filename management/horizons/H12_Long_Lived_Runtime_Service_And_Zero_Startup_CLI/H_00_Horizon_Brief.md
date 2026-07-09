# H_00 Horizon Brief

Owner: cli-profile-manager
Source of Truth: management/horizons/H12_Long_Lived_Runtime_Service_And_Zero_Startup_CLI/README.md
Lifecycle: living
Document Class: brief

Status: planned.

## Context

H10 separates Python startup, imports, parser work, and command execution. If
the host Python runtime remains the largest unavoidable cost, command latency
cannot be solved entirely inside one-shot process execution.

## Problem

A fast in-process command handler can still feel slow if every command pays a
multi-second host process startup penalty. A long-lived runtime can amortize
imports, parser setup, profile discovery, and quota scheduler setup, but it adds
state, lifecycle, and security concerns.

## Strategy

Treat the long-lived runtime as optional and evidence-driven. Build it only
after H10/H11 establish that command code is already efficient and startup
dominates user-perceived latency.
