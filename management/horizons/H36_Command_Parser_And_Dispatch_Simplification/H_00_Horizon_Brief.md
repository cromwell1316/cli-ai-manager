# H_00 Horizon Brief

Owner: cli-profile-manager
Source of Truth: management/horizons/H36_Command_Parser_And_Dispatch_Simplification/README.md
Lifecycle: living
Document Class: brief

Status: planned.

## Context

The command layer has grown compatibility wrappers and duplicated dispatch
surfaces.

## Problem

Extra indirection increases startup complexity and makes optimization harder.

## Strategy

Simplify parser and dispatch internals while preserving all public commands and
structured operation results.
