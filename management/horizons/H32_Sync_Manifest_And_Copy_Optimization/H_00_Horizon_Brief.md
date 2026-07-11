# H_00 Horizon Brief

Owner: cli-profile-manager
Source of Truth: management/horizons/H32_Sync_Manifest_And_Copy_Optimization/README.md
Lifecycle: living
Document Class: brief

Status: implemented.

## Context

Sync already limits known profile files, but planning and hard-mode deletion can
still traverse more than necessary.

## Problem

Large profile homes and Windows paths make sync planning expensive.

## Strategy

Build explicit manifests and use manifest diffs for copy, skip, and delete
decisions.
