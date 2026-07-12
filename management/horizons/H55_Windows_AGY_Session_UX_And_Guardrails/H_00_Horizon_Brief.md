# H_00 Horizon Brief

Owner: cli-profile-manager
Source of Truth: management/horizons/H55_Windows_AGY_Session_UX_And_Guardrails/README.md
Lifecycle: living
Document Class: brief

Status: planned.

## Context

Native Windows AGY relies on one Credential Manager target per Windows user.
Profile backups can be swapped into that live slot, but same-user true parallel
isolation is not available.

## Problem

Without explicit UX guardrails, users can misunderstand Windows AGY as equivalent
to WSL HOME-based isolation.

## Strategy

Expose live-slot state, backup state, serialization policy, and recovery actions
directly in the Windows AGY workflows.

## Expected Result

Windows AGY launches are understandable, serialized where needed, and recoverable
without exposing token material.

