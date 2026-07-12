# H_00 Horizon Brief

Owner: cli-profile-manager
Source of Truth: management/horizons/H45_Windows_AGY_Quota_Backend/README.md
Lifecycle: living
Document Class: brief

Status: implemented.

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

## Result

Native Windows AGY quota now uses a helper-backed direct prompt probe instead
of Unix PTY startup. The selected profile is inferred from `pN` cwd, the helper
applies `cred-pN.json`, and successful prompt completion returns the existing
AGY availability payload with a warning that percentages are unavailable from
this probe. Missing backup, missing CLI, PowerShell absence, timeouts, and AGY
runtime failures are mapped to explicit quota states.
