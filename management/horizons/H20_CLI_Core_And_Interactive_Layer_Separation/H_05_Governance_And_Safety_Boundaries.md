# H_05 Governance And Safety Boundaries

Owner: cli-profile-manager
Source of Truth: management/horizons/H20_CLI_Core_And_Interactive_Layer_Separation/README.md
Lifecycle: living
Document Class: governance

Status: implemented.

## Boundaries

- Core operation modules must not print terminal UI.
- CLI parsing must not contain business logic when a core operation exists.
- Interactive UI must not bypass safety, audit, or invalidation hooks.
- Compatibility exports must be removed only with an explicit migration plan.
