# V_04 PTY Pipeline Verification

Owner: cli-profile-manager
Source of Truth: management/horizons/H09_Performance_Runtime_Optimization_And_Async_Scaling/README.md
Lifecycle: living
Document Class: validation

Status: implemented.

## Checks

- Cold and warm PTY probe timings are measured separately.
- Readiness detection is tested against captured terminal transcripts.
- Session TTL and max-session cleanup are deterministic.
- Parser miss invalidation still works.
- Token redaction remains enforced.

## Evidence

- Persistent quota sessions now track creation and last-used times.
- `AI_MAN_QUOTA_SESSION_TTL_SECONDS` bounds idle session lifetime and
  `AI_MAN_QUOTA_SESSION_MAX` bounds total persistent sessions.
- `evict_persistent_quota_sessions` removes dead, idle, and excess sessions
  before new persistent quota probes are started.
- Diagnostics session snapshots include created and idle ages without exposing
  token values.
- Tests cover session reuse, per-profile separation, dead-session replacement,
  timeout invalidation, parser-miss invalidation, TTL eviction, and max-count
  eviction.
