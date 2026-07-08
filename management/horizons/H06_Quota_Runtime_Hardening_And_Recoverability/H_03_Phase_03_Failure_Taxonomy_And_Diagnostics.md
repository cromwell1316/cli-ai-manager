# H_03 Phase 03 Failure Taxonomy And Diagnostics

Owner: cli-profile-manager
Source of Truth: management/horizons/H06_Quota_Runtime_Hardening_And_Recoverability/README.md
Lifecycle: living
Document Class: implementation phase

Status: implemented.

## Objective

Replace generic `unknown` quota failures with precise, actionable states.

## Scope

- Distinguish empty output from captured-but-unmatched output.
- Preserve a short sanitized diagnostic summary in JSON payloads.
- Keep long raw terminal output out of normal table rendering.
- Ensure authentication prompts map to `auth_required`.
- Ensure missing native CLI maps to `missing_cli`.

## Acceptance

- `parse_quota()` returns `empty_output` for empty or whitespace-only output.
- `parse_quota()` returns `parser_miss` for non-empty unmatched quota output.
- JSON quota payloads include warnings that explain the state.
- Interactive AGY columns show compact markers while diagnostics stay available
  through JSON/noninteractive quota commands.
