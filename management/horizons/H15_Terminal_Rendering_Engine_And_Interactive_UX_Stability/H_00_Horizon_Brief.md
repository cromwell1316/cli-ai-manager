# H_00 Horizon Brief

Owner: cli-profile-manager
Source of Truth: management/horizons/H15_Terminal_Rendering_Engine_And_Interactive_UX_Stability/README.md
Lifecycle: living
Document Class: brief

Status: implemented.

## Context

Interactive screens currently combine command behavior, layout generation, ANSI
control sequences, and keyboard loops. The status screen has a diff renderer,
but other screens still rely on full clears and direct printing.

## Problem

Full-screen clears cause flicker, make output harder to inspect, and increase
the chance of broken terminal state after exceptions. As more live behavior is
added, inconsistent rendering will become harder to test and maintain.

## Strategy

Create a small terminal rendering layer that owns frame painting, cursor
visibility, cleanup, line diffing, table layout, and TTY fallback behavior.
Migrate screens incrementally while keeping command behavior unchanged.
