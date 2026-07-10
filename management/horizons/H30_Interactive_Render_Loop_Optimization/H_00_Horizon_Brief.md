# H_00 Horizon Brief

Owner: cli-profile-manager
Source of Truth: management/horizons/H30_Interactive_Render_Loop_Optimization/README.md
Lifecycle: living
Document Class: brief

Status: planned.

## Context

The interactive screen redraw path is acceptable today but can become noisy
with many profiles, quota updates, and developer mode enabled.

## Problem

Full redraws and repeated formatting can waste work when the visible state has
not changed.

## Strategy

Cache render inputs and formatted rows, then redraw only meaningful changes.
