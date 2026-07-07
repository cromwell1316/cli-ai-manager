# H_05 Governance And Safety Boundaries

Owner: cli-profile-manager
Source of Truth: management/horizons/H02_Keyboard_First_Profile_Command_Surface/README.md
Lifecycle: living
Document Class: governance

Status: planned.

## Command Safety

Commands that mutate profile data must print the target path before writing.
Destructive commands require explicit confirmation unless `--yes` is supplied.

## API Boundary

Interactive UI must call the same functions as direct commands. No second logic
copy is allowed for status, import, export, launch, or clear.

## Dependency Boundary

The command surface remains Python standard library only.
