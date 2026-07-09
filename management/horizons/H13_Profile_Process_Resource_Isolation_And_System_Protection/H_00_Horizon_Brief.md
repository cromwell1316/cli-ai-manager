# H_00 Horizon Brief

Owner: cli-profile-manager
Source of Truth: management/horizons/H13_Profile_Process_Resource_Isolation_And_System_Protection/README.md
Lifecycle: living
Document Class: brief

Status: implemented.

## Context

The profile manager launches native CLIs and also starts PTY subprocesses for
quota probing. These child processes can outlive a command path or become
expensive under multiple profiles. The main application should remain
responsive even when one profile's native CLI becomes memory-heavy or CPU-heavy.

## Problem

Without explicit process limits, a single launched profile or a group of quota
probes can consume enough system resources to affect the whole machine. This is
especially risky when multiple profiles are active, persistent PTY sessions are
enabled, or native CLIs spawn helper processes.

## Strategy

Create one process-launch abstraction with resource policies, then route launch
and quota subprocess creation through it. Use strong OS backends when available
and predictable soft fallbacks otherwise.
