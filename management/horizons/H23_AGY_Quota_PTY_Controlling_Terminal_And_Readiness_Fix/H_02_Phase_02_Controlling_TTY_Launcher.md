# H_02 Phase 02 Controlling TTY Launcher

Owner: cli-profile-manager
Source of Truth: management/horizons/H23_AGY_Quota_PTY_Controlling_Terminal_And_Readiness_Fix/README.md
Lifecycle: living
Document Class: implementation phase

Status: implemented.

## Objective

Make quota PTY subprocesses run with a proper controlling terminal.

## Scope

- Add a shared PTY launch helper for quota probes.
- In the child process, call `setsid` and assign the slave PTY as controlling
  terminal with `TIOCSCTTY` before exec.
- Preserve existing process policy behavior and resource limits.
- Ensure file descriptors are closed correctly in parent and child paths.
- Keep Windows behavior as unsupported unless a Windows PTY backend is added.
- Add diagnostics for controlling-terminal setup failures.

## Acceptance

- Fake CLIs that require `/dev/tty` can start under the quota launcher.
- Resource policy integration still works.
- Startup failures include the controlling-terminal setup stage when relevant.
