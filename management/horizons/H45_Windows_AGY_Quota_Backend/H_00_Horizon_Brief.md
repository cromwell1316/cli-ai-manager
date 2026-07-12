# H_00 Horizon Brief

Owner: cli-profile-manager
Source of Truth: management/horizons/H45_Windows_AGY_Quota_Backend/README.md
Lifecycle: living
Document Class: brief

Status: planned.

## Context

Native Windows AGY launch now uses a managed Credential Manager helper, but the
quota path still assumes Unix PTY behavior. That leaves Windows installs without
full quota parity.

## Problem

`ai-man status agy pN --quota` and `ai-man quota agy pN` need to select the
same Windows credential backup as launch/login before asking AGY for usage
state.

## Strategy

Introduce a Windows-specific quota backend that delegates credential switching
to the managed helper and returns the existing quota payload contract.

## Expected Result

Windows AGY quota commands work without Unix-only terminal primitives and
produce actionable errors for missing token, missing CLI, timeout, and auth
states.
