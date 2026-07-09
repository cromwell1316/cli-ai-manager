# V_01 Boundary Verification

Owner: cli-profile-manager
Source of Truth: management/horizons/H20_CLI_Core_And_Interactive_Layer_Separation/README.md
Lifecycle: living
Document Class: validation

Status: planned.

## Verification

- Core operation modules do not import interactive rendering.
- CLI handlers are thin wrappers around operations.
- Interactive workflows use operation APIs.
- Audit, safety, config, and invalidation hooks are not bypassed.
