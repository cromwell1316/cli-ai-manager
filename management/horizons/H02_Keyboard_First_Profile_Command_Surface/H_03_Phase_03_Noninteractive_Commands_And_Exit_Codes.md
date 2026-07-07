# H_03 Phase 03 Noninteractive Commands And Exit Codes

Owner: cli-profile-manager
Source of Truth: management/horizons/H02_Keyboard_First_Profile_Command_Surface/README.md
Lifecycle: living
Document Class: phase

Status: implemented.

## Scope

Make core operations callable without the interactive selector.

## Required Behavior

- Every command has stable stdout/stderr behavior.
- Missing CLI executable returns non-zero with a clear error.
- Missing token returns non-zero for operations that require a token.
- Import/export parse failures return non-zero and do not write partial files.
- `--json` output is available for list/status to support automation.

## Phase Exit

The main workflows can be tested with subprocess calls rather than terminal key
simulation.
