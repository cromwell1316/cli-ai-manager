# H_00 Horizon Brief

Owner: cli-profile-manager
Source of Truth: management/horizons/H46_Windows_Interactive_Surface/README.md
Lifecycle: living
Document Class: brief

Status: implemented.

## Context

The interactive selector is currently built around Unix terminal primitives.
Native Windows direct commands work, but `ai-man` with no arguments falls back
to a command list instead of a selector.

## Problem

Windows users should get a usable interactive manager without importing
`termios`, `tty`, or Unix-only `select` behavior.

## Strategy

Split terminal input/rendering behind platform adapters and implement a native
Windows adapter while preserving the WSL/Linux renderer.

## Expected Result

Native Windows users can navigate the same core workflows from `ai-man` without
losing direct-command compatibility.

## Result

Native Windows now has a dedicated console selector. It uses numbered prompts
instead of Unix raw-mode keyboard handling, which keeps startup free of
Unix-only terminal imports while still exposing the core profile workflows.
Direct commands remain available and WSL/Linux continues to use the existing
keyboard renderer.
