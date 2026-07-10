# V_02 Tmux Session Verification

Owner: cli-profile-manager
Source of Truth: management/horizons/H24_AGY_Quota_Tmux_Backend_And_Terminal_Parity/README.md
Lifecycle: living
Document Class: validation

Status: implemented.

## Session Creation

Verify tmux is called with:

```text
new-session -d
-s <manager_owned_session>
-c /home/olivercromwell
env HOME=/home/olivercromwell/agy-homes/pN agy
```

## Session Naming

Verify names:

- start with `ai_man_quota_`;
- include tool/profile information;
- contain no raw slashes;
- remain stable for the same profile identity;
- differ across profile homes.

## Read And Write Operations

Verify:

- `capture-pane` reads output;
- `send-keys` sends `/usage`;
- `send-keys` can send `Escape` after capture;
- dead sessions are detected through `has-session`.

## Isolation

Start p1 and p2. Verify:

- p1 and p2 use different tmux sessions;
- p1 `HOME` is p1 home;
- p2 `HOME` is p2 home;
- commands sent to p1 do not affect p2.

## Registry

Verify the in-process registry can show:

- session count;
- cwd;
- home;
- created age;
- idle age;
- alive state.
