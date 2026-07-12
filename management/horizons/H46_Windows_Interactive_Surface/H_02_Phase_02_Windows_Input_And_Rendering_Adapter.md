# H_02 Phase 02 Windows Input And Rendering Adapter

Owner: cli-profile-manager
Source of Truth: management/horizons/H46_Windows_Interactive_Surface/README.md
Lifecycle: living
Document Class: horizon-phase

Status: planned.

## Objective

Implement native Windows keyboard input and rendering support.

## Deliverables

- Windows key reader for arrows, enter, escape, and shortcut keys.
- Rendering path that works in PowerShell and Windows Terminal.
- Graceful fallback for limited terminals.
- Tests for adapter selection and key normalization.

## Validation Focus

- Menu navigation works without Unix raw-mode APIs.
- Text output remains readable in common Windows shells.
