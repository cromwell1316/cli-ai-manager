# H_05 Governance And Safety Boundaries

Owner: cli-profile-manager
Source of Truth: management/horizons/H11_Status_IO_Indexing_And_Command_Cache_Performance/README.md
Lifecycle: living
Document Class: governance

Status: planned.

## Boundaries

- Cache derived status data only inside a command unless invalidation is proven.
- Never cache raw credential contents for performance.
- Keep diagnostics redaction mandatory.
- Prefer measured simplification over speculative indexes.
