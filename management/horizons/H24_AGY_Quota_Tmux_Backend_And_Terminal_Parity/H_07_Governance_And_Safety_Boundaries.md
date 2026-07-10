# H_07 Governance And Safety Boundaries

Owner: cli-profile-manager
Source of Truth: management/horizons/H24_AGY_Quota_Tmux_Backend_And_Terminal_Parity/README.md
Lifecycle: living
Document Class: governance

Status: implemented.

## Safety Boundaries

- Do not read or print raw OAuth tokens.
- Do not modify AGY credential files.
- Do not clear browser profiles.
- Do not kill user tmux sessions.
- Do not remove user files from profile homes.
- Do not disable quota visibility for all tools to work around AGY.
- Do not treat eligibility warning text as proof that the account is unusable.

## Ownership Boundary

The tmux backend owns only sessions it creates with the manager prefix:

```text
ai_man_quota_
```

All cleanup must be scoped to registry entries or exact session names with that
prefix.

## Behavioral Boundary

The backend is responsible for terminal orchestration only. It must not change:

- credential model;
- profile numbering;
- account detection;
- sync behavior;
- launch behavior;
- Codex/Claude quota behavior.

## Logging Boundary

Logs may include:

- profile number;
- profile home path;
- backend;
- session name;
- high-level AGY diagnostic summary.

Logs must not include:

- token values;
- cookie contents;
- browser local storage contents;
- full credential JSON.

## Review Boundary

Before implementation is accepted, review must specifically check:

- no broad tmux kill commands;
- no raw token logging;
- fallback mode works;
- forced tmux mode fails clearly;
- tests cover lifecycle cleanup.
