# H_05 Governance And Safety Boundaries

Owner: cli-profile-manager
Source of Truth: management/horizons/H08_Distribution_Configuration_And_User_Experience_Polish/README.md
Lifecycle: living
Document Class: governance

Status: planned.

## Boundaries

- Do not break existing command names, JSON fields, or profile paths without a
  documented migration.
- Install changes must be idempotent.
- Rendering changes must be covered by tests with ANSI-colored content.
- UX polish must not remove diagnostic detail from JSON output.
