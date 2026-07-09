# H_02 Phase 02 Command Snapshot Model

Owner: cli-profile-manager
Source of Truth: management/horizons/H11_Status_IO_Indexing_And_Command_Cache_Performance/README.md
Lifecycle: living
Document Class: implementation phase

Status: planned.

## Objective

Introduce a command-scoped snapshot object that carries profile discovery,
metadata, status payloads, and account lookup results through one command.

## Scope

- Define a lightweight snapshot structure with explicit fields.
- Reuse the snapshot across table rendering and JSON output.
- Keep direct helper APIs compatible.
- Avoid global mutable cache for correctness.

## Acceptance

- One command execution performs one profile discovery pass per relevant tool.
- Rendering does not trigger new status/account reads.
- Existing CLI and interactive tests still pass.
