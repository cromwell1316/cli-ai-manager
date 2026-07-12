# H_00 Horizon Brief

Owner: cli-profile-manager
Source of Truth: management/horizons/H53_Unified_Interactive_Renderer_For_Windows_And_WSL/README.md
Lifecycle: living
Document Class: brief

Status: completed.

## Context

WSL and native Windows currently have separate interactive implementations. The
WSL surface is richer, while the Windows surface is a conservative fallback.

## Problem

Duplicated menu definitions cause drift in labels, shortcuts, routing, and
visual behavior.

## Strategy

Move menu definitions and action routing into shared descriptors, then render
those descriptors through small platform adapters.

## Expected Result

Windows and WSL expose the same interactive workflows while keeping terminal
handling platform-appropriate.

