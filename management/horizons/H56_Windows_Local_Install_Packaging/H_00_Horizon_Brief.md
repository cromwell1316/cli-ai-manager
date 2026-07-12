# H_00 Horizon Brief

Owner: cli-profile-manager
Source of Truth: management/horizons/H56_Windows_Local_Install_Packaging/README.md
Lifecycle: living
Document Class: brief

Status: planned.

## Context

Development installs can point Windows shims at `\\wsl.localhost` paths, but a
daily Windows install should not depend on WSL availability.

## Problem

UNC-backed installs are fragile when WSL is stopped, renamed, or the repository
is moved.

## Strategy

Create a Windows-local source/runtime layout and point shims at that stable
location.

## Expected Result

Native Windows `ai-man` works from a Windows-local install even when WSL is not
available.

