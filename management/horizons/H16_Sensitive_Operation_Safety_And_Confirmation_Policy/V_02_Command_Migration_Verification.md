# V_02 Command Migration Verification

Owner: cli-profile-manager
Source of Truth: management/horizons/H16_Sensitive_Operation_Safety_And_Confirmation_Policy/README.md
Lifecycle: living
Document Class: validation

Status: planned.

## Verification

- Clear, sync, import, export, label, login, launch, service, and audit purge
  paths use the policy layer.
- Interactive and CLI paths share policy decisions.
- Mutating commands invalidate relevant caches after successful completion.
- Partial failures produce recovery guidance.
