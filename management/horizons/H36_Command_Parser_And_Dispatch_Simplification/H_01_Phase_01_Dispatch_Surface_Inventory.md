# H_01 Phase 01 Dispatch Surface Inventory

Owner: cli-profile-manager
Source of Truth: management/horizons/H36_Command_Parser_And_Dispatch_Simplification/README.md
Lifecycle: living
Document Class: horizon-phase

Status: implemented.

## Objective

Inventory parser, dispatch, wrapper, and operation boundaries.

## Deliverables

- Command handler map.
- Duplicate wrapper list.
- Heavy command boundary list.
- Behavior equivalence requirements.

## Result

The dispatch surface is represented by `COMMAND_HANDLERS`. Parser defaults now
store stable handler names, while compatibility wrappers and lazy helper module
boundaries remain available for public API callers.
