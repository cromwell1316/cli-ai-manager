# H_00 Horizon Brief

Owner: cli-profile-manager
Source of Truth: management/horizons/H27_Runtime_Service_Acceleration/README.md
Lifecycle: living
Document Class: brief

Status: implemented.

## Context

The runtime service exists to amortize startup and reuse read-only state.

## Problem

The service must become measurably faster than one-shot execution while keeping
fallback behavior and invalidation correct.

## Strategy

Accelerate read-only commands through cached state and explicit mutation-driven
invalidation.

## Outcome

The runtime service now keeps an in-process response cache and a reusable
generation-scoped command snapshot for stable read-only commands, clears both on
mutation-driven invalidation, and exposes cache and latency metrics through
service health.
