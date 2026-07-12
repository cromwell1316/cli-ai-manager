# H55 Acceptance Matrix

Owner: cli-profile-manager
Source of Truth: management/horizons/H55_Windows_AGY_Session_UX_And_Guardrails/README.md
Lifecycle: living
Document Class: validation

Status: completed.

| Area | Acceptance |
| --- | --- |
| Shared slot | UI clearly states same-user native Windows AGY is serialized. |
| Recovery | Missing or stale credential state has an actionable recovery path. |
| Locking | Concurrent shared-slot attempts produce clear guidance. |
| Safety | No token blobs are printed in UI, logs, or tests. |
| Diagnostics | Token-safe guardrail state is available in diagnostics. |
| Interactive UX | Windows interactive and direct CLI use the same guardrail model. |
