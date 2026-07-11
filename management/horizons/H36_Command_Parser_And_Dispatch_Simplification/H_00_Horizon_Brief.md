# H_00 Horizon Brief

Owner: cli-profile-manager
Source of Truth: management/horizons/H36_Command_Parser_And_Dispatch_Simplification/README.md
Lifecycle: living
Document Class: brief

Status: implemented.

## Context

The command layer has grown compatibility wrappers and duplicated dispatch
surfaces.

## Problem

Extra indirection increases startup complexity and makes optimization harder.

## Strategy

Simplify parser and dispatch internals while preserving all public commands and
structured operation results.

## Result

Commands now resolve through an explicit handler table instead of storing
function objects directly in argparse defaults. Public command grammar remains
unchanged.
