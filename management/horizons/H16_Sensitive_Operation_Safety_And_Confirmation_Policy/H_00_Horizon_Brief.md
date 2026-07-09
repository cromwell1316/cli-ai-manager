# H_00 Horizon Brief

Owner: cli-profile-manager
Source of Truth: management/horizons/H16_Sensitive_Operation_Safety_And_Confirmation_Policy/README.md
Lifecycle: living
Document Class: brief

Status: implemented.

## Context

The application manages credentials, profile directories, Windows/WSL sync, and
native CLI sessions. Several commands can mutate or delete important local data.

## Problem

Safety behavior is implemented per command. This makes it easy for a new command
to miss a confirmation, skip a dry-run path, or report recovery steps
inconsistently.

## Strategy

Introduce a reusable sensitive-operation policy with risk levels, preflight
results, confirmation requirements, and audit hooks. Migrate mutating commands
onto that policy while preserving existing CLI flags.
