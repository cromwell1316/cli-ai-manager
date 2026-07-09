# H_00 Horizon Brief

Owner: cli-profile-manager
Source of Truth: management/horizons/H20_CLI_Core_And_Interactive_Layer_Separation/README.md
Lifecycle: living
Document Class: brief

Status: planned.

## Context

The CLI module still owns parsing, command behavior, formatting, compatibility
exports, and functions consumed by interactive workflows.

## Problem

When UI code imports broad CLI internals, behavior becomes harder to reuse and
test. Cross-cutting concerns like audit, safety policy, config, and runtime
invalidation need a cleaner operation boundary.

## Strategy

Introduce core operation modules and result envelopes, then migrate CLI and
interactive layers to call the same operation APIs.
