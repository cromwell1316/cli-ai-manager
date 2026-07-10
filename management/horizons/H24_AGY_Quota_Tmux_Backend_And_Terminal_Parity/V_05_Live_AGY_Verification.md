# V_05 Live AGY Verification

Owner: cli-profile-manager
Source of Truth: management/horizons/H24_AGY_Quota_Tmux_Backend_And_Terminal_Parity/README.md
Lifecycle: living
Document Class: validation

Status: implemented.

## Preconditions

- `tmux` is installed.
- AGY CLI is installed.
- AGY profile homes exist.
- At least p1 has valid token files.

## Single Profile

Run:

```bash
python3 -m cli_profile_manager.cli quota agy p1 --json
```

Expected:

- backend is tmux in logs;
- no false terminal `auth_required`;
- `/usage` is sent;
- quota output includes account and model quota fields when available.

## Multiple Profiles

Run the interactive status refresh or an equivalent command path that enqueues
p1-p11.

Expected:

- each profile gets its own tmux session;
- no session cross-talk;
- no burst of false `auth_required`;
- queued jobs finish or remain retryable rather than terminally failed.

## Log Review

Fresh log should show:

```text
backend=tmux
cwd=/home/olivercromwell
home=/home/olivercromwell/agy-homes/pN
quota command sent tool=agy command=/usage
```

It should not repeatedly show:

```text
AGY CLI could not complete sign-in for this profile; /usage was not sent
```

for token-bearing profiles that work manually.

## Cleanup

After exiting the manager or expiring sessions:

```bash
tmux ls
```

Expected:

- no stale `ai_man_quota_` sessions unless a live manager process owns them.
