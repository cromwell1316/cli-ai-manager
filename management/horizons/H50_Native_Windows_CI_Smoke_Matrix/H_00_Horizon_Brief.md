# H_00 Horizon Brief

Owner: cli-profile-manager
Source of Truth: management/horizons/H50_Native_Windows_CI_Smoke_Matrix/README.md
Lifecycle: living
Document Class: brief

Status: planned.

## Context

Most development and tests run from WSL/Linux, while Windows support now has
native installer and credential helper behavior.

## Problem

Windows regressions can slip through if CI never executes native Windows smoke
checks.

## Strategy

Add a Windows CI job that verifies syntax, focused tests, installer shims, and
helper generation without requiring real tokens.

## Expected Result

Pull requests receive native Windows signal for command surface and installer
regressions.
