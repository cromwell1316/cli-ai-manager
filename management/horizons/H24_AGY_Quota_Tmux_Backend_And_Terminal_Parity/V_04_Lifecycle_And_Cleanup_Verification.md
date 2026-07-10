# V_04 Lifecycle And Cleanup Verification

Owner: cli-profile-manager
Source of Truth: management/horizons/H24_AGY_Quota_Tmux_Backend_And_Terminal_Parity/README.md
Lifecycle: living
Document Class: validation

Status: implemented.

## Close

When a tmux-backed AGY quota session is closed, verify:

```text
tmux kill-session -t <session>
```

is called exactly for the manager-owned session.

## TTL Eviction

Set a short TTL. Verify idle manager-owned sessions are evicted and killed.

## Max Count Eviction

Set a low max count. Start multiple AGY profile sessions. Verify oldest idle
sessions are evicted first.

## Starting Session Protection

Verify a session inside its startup window is not evicted merely because the max
count check runs while it is starting.

## Dead Session Recovery

Kill a manager-owned tmux session externally. The next quota request should:

- detect the dead session;
- remove it from the registry;
- create a new session;
- not reuse stale output.

## Parser Miss Threshold

Force repeated parser miss output. Verify the session is invalidated after the
existing parser miss threshold and then recreated on the next request.

## Exit Cleanup

Trigger process cleanup. Verify manager-owned tmux sessions are closed through
the registered cleanup path.
