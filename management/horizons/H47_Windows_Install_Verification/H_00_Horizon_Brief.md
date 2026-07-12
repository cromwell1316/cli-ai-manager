# H_00 Horizon Brief

Owner: cli-profile-manager
Source of Truth: management/horizons/H47_Windows_Install_Verification/README.md
Lifecycle: living
Document Class: brief

Status: implemented.

## Context

Windows installation now has a dedicated PowerShell installer, but users need a
repeatable way to verify that the installation is operational.

## Problem

Failures such as missing Python, stale PATH, missing helper, or blocked
Credential Manager access should be reported by a single post-install command.

## Strategy

Add a Windows verification script that checks shims, PATH, Python, helper
generation, and safe Credential Manager access.

## Expected Result

Windows users can validate or troubleshoot installation without manually
inspecting generated files.

## Result

Native Windows installs now have a deterministic PowerShell verifier. It checks
the generated shims, PATH state, Python/PowerShell availability, managed AGY
helper freshness, and Credential Manager API access while avoiding real profile
credentials.
