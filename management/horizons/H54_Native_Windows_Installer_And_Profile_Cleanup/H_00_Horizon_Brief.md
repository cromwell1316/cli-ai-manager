# H_00 Horizon Brief

Owner: cli-profile-manager
Source of Truth: management/horizons/H54_Native_Windows_Installer_And_Profile_Cleanup/README.md
Lifecycle: living
Document Class: brief

Status: completed.

## Context

Native Windows install can be affected by broken Python launchers, execution
policy, stale profile functions, and old multiaccount scripts.

## Problem

Users can install the shims successfully but still launch the wrong function or
see startup errors from PowerShell profile dot-sourcing.

## Strategy

Add explicit profile conflict detection, cleanup guidance, and installer
verification that reports actionable remediation steps.

## Expected Result

Opening PowerShell and running `ai-man` uses the installed application without
profile startup errors or stale aliases.
