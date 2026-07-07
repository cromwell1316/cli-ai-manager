# V_04 Acceptance Matrix

Owner: cli-profile-manager
Source of Truth: management/horizons/H01_TUI_Surface_Removal_And_CLI_Core_Cleanup/README.md
Lifecycle: living
Document Class: acceptance matrix

Status: planned.

| Phase | Acceptance Evidence |
| --- | --- |
| Phase 01 Surface Inventory | TUI files, launchers, imports, and docs are enumerated; protected data is excluded |
| Phase 02 TUI Removal | Supported runtime has no Textual/Rich imports or TUI entrypoints |
| Phase 03 Docs Install Cleanup | README and install script describe CLI-only usage and install only CLI links |

## Done Definition

H01 is complete when all supported TUI code paths and launchers are gone, the
remaining CLI compiles and installs, docs match the CLI-only product, and a
search check prevents accidental TUI reintroduction.
