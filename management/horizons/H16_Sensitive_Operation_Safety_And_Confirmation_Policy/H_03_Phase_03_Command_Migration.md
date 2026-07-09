# H_03 Phase 03 Command Migration

Owner: cli-profile-manager
Source of Truth: management/horizons/H16_Sensitive_Operation_Safety_And_Confirmation_Policy/README.md
Lifecycle: living
Document Class: implementation phase

Status: planned.

## Objective

Move all sensitive commands and interactive flows onto the shared policy.

## Scope

- Migrate clear profile, sync, import, export, label, login/add profile, launch,
  service stop, and audit purge.
- Keep backwards-compatible flags where possible.
- Ensure JSON output includes policy decisions and preflight facts.
- Ensure interactive prompts use the same policy as noninteractive commands.

## Acceptance

- No mutating command bypasses the policy.
- Tests cover `--dry-run`, `--yes`, prompt refusal, and success paths.
- Existing command behavior remains compatible except where safety requires an
  explicit documented change.
