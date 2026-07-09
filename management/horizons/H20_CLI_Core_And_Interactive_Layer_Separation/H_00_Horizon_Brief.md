# H_00 Horizon Brief

Owner: cli-profile-manager
Source of Truth: management/horizons/H20_CLI_Core_And_Interactive_Layer_Separation/README.md
Lifecycle: living
Document Class: brief

Status: implemented.

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

## Outcome

The shared operation boundary now lives in `cli_profile_manager.operations`.
CLI handlers delegate command behavior to operations and retain output
formatting, safety prompts, and audit wiring. Interactive workflows use the
same operation helpers for profile, credential, sync, quota, and metadata
behavior.
