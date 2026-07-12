# H_00 Horizon Brief

Owner: cli-profile-manager
Source of Truth: management/horizons/H51_Credential_Recovery_And_Backup_UX/README.md
Lifecycle: living
Document Class: brief

Status: planned.

## Context

Windows AGY support relies on managed credential backups plus a single live
Credential Manager slot. Users need safe recovery commands instead of manual
PowerShell edits.

## Problem

Restoring, inspecting, or clearing the live AGY credential slot is sensitive and
must be audited, confirmed, and token-safe.

## Strategy

Add explicit command surface for managed backup inspection and live slot
recovery using existing safety and audit boundaries.

## Expected Result

Users can recover AGY credential state from managed backups without exposing
tokens or editing helper scripts.
