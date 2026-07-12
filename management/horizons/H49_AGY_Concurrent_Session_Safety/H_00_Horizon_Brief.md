# H_00 Horizon Brief

Owner: cli-profile-manager
Source of Truth: management/horizons/H49_AGY_Concurrent_Session_Safety/README.md
Lifecycle: living
Document Class: brief

Status: implemented.

## Context

Native Windows AGY stores the active account in one shared Credential Manager
target per Windows user. The manager can switch that slot at launch time, but
true parallel safety depends on AGY runtime behavior.

## Problem

If AGY rereads or refreshes the shared slot during an active session, multiple
windows may cross accounts.

## Strategy

Run reproducible concurrency drills, document observed behavior, and add
guardrails or warnings that match the evidence.

## Expected Result

Windows AGY concurrency has a documented policy, diagnostic support, and a
clear recovery path.

## Result

Implemented a conservative `serialized_shared_slot` policy. Native Windows AGY
launch/login flows in one Windows user are guarded by a named mutex, diagnostics
surface the policy and recovery commands, and docs state that true parallel
isolation requires separate Windows users.
