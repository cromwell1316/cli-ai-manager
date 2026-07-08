# V_02 Persistent Session Verification

Owner: cli-profile-manager
Source of Truth: management/horizons/H05_AGY_Quota_Loading_Reliability_And_Status_UX/README.md
Lifecycle: living
Document Class: validation

Status: planned.

## Required Checks

- Repeated refreshes for one AGY profile reuse one live session.
- Separate AGY profiles do not share one session.
- Dead sessions are replaced before the next refresh.
- Explicit invalidation closes related sessions.

## Evidence

Pending implementation.
