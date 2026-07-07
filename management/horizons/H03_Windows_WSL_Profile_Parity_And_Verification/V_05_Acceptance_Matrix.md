# V_05 Acceptance Matrix

Owner: cli-profile-manager
Source of Truth: management/horizons/H03_Windows_WSL_Profile_Parity_And_Verification/README.md
Lifecycle: living
Document Class: acceptance matrix

Status: planned.

| Phase | Acceptance Evidence |
| --- | --- |
| Phase 01 Credential Model | Windows and WSL credential authority documented and reflected in code |
| Phase 02 Status Detection | Token status matches authoritative platform files and invalid JSON fails |
| Phase 03 Conversion | Synthetic fixtures convert Windows -> WSL and WSL -> Windows |
| Phase 04 Launch And Sync | Dry-run launch/sync shows correct platform behavior and conversion plan |

## Done Definition

H03 is complete when Windows and WSL profile behavior matches their real
credential models, status cannot produce known false active/no-token reports,
credential conversion is fixture-tested, and sync/launch dry-runs make the
platform-specific behavior visible.
