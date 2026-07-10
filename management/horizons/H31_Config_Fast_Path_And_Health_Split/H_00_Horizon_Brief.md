# H_00 Horizon Brief

Owner: cli-profile-manager
Source of Truth: management/horizons/H31_Config_Fast_Path_And_Health_Split/README.md
Lifecycle: living
Document Class: brief

Status: planned.

## Context

`config show` should be a pure view of effective settings, but it can drift
toward health and diagnostics work.

## Problem

Health checks make config slower and blur command responsibilities.

## Strategy

Keep config resolution pure and move heavier checks into explicit health or
doctor flows.
