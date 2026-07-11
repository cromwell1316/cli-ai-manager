# H_01 Phase 01 Lookup Surface Inventory

Owner: cli-profile-manager
Source of Truth: management/horizons/H41_Executable_Lookup_Cache/README.md
Lifecycle: living
Document Class: horizon-phase

Status: planned.

## Objective

Identify executable lookup sites worth caching.

## Deliverables

- Inventory of `shutil.which` and equivalent lookup calls.
- Hot-path classification for each lookup.
- Cache eligibility decision for each site.
- Risk notes for explicit executable paths.

## Implementation Notes

- Cache only lookups that depend on command name and `PATH`.
- Leave one-off or already-cheap lookup sites unchanged unless evidence says
  otherwise.
