# H_00 Horizon Brief

Owner: cli-profile-manager
Source of Truth: management/horizons/H28_Profile_Index_And_Filesystem_Snapshot/README.md
Lifecycle: living
Document Class: brief

Status: planned.

## Context

Profile status commands repeatedly scan profile roots and credential files.

## Problem

Repeated filesystem work adds latency and becomes worse with more profiles or
slow WSL/Windows paths.

## Strategy

Introduce command-scoped and service-scoped indexes that cache facts, not raw
credentials.
