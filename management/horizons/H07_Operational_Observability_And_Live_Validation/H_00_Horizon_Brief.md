# H_00 Horizon Brief

Owner: cli-profile-manager
Source of Truth: management/horizons/H07_Operational_Observability_And_Live_Validation/README.md
Lifecycle: living
Document Class: horizon brief

Status: implemented.

## Problem

When quota loading fails on a real machine, the current project has limited ways
to answer basic operational questions: which jobs are queued, which sessions are
alive, which profile failed, what failure class occurred, and whether the native
CLI is reachable.

## Desired End State

Operators should be able to run one safe diagnostics command and get a useful
summary without exposing credentials. Live AGY validation should be repeatable
and produce evidence that can be checked into horizon notes when sanitized.
