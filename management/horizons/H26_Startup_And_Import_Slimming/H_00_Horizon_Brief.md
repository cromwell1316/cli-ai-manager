# H_00 Horizon Brief

Owner: cli-profile-manager
Source of Truth: management/horizons/H26_Startup_And_Import_Slimming/README.md
Lifecycle: living
Document Class: brief

Status: implemented.

## Context

In-process command handlers are fast, but one-shot CLI commands still pay
Python startup, imports, and parser construction.

## Problem

Common read-only commands load more application surface than they need.

## Strategy

Profile imports, keep common commands on minimal import paths, and defer heavy
modules until command execution requires them.
