# H_00 Horizon Brief

Owner: cli-profile-manager
Source of Truth: management/horizons/H48_Cross_Platform_Sync_E2E/README.md
Lifecycle: living
Document Class: brief

Status: planned.

## Context

Sync can convert AGY credentials between WSL OAuth files and Windows backup
files, but full end-to-end parity needs broader scenario coverage.

## Problem

Users need confidence that sync direction, dry-run, soft mode, hard mode, and
metadata preservation work across Windows and WSL roots.

## Strategy

Build deterministic fixtures and scenario tests that validate both sync
directions without mutating the live Windows Credential Manager slot.

## Expected Result

Profile roots can be synchronized safely in either direction with clear dry-run
plans and predictable credential conversion.
