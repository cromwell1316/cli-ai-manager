# H_00 Horizon Brief

Owner: cli-profile-manager
Source of Truth: management/horizons/H18_Configuration_Surface_Consolidation_And_Effective_Settings_UX/README.md
Lifecycle: living
Document Class: brief

Status: implemented.

## Context

The application is controlled by many environment variables and internal
defaults across quota, runtime, process policy, audit, paths, and rendering.

## Problem

Users and maintainers need a single way to answer what setting is active, where
it came from, whether it is valid, and whether it is safe to display.

## Strategy

Build a config registry with typed setting definitions, source tracking,
validation, redaction, and command/diagnostics integration.

## Implementation Evidence

Implemented a source-aware config registry and connected it to `config show`
and diagnostics while keeping existing env names working.
