# H_04 Phase 04 Command Dispatch And Quota Capture

Owner: cli-profile-manager
Source of Truth: management/horizons/H24_AGY_Quota_Tmux_Backend_And_Terminal_Parity/README.md
Lifecycle: living
Document Class: horizon-phase

Status: implemented.

## Objective

Send `/usage` through tmux and capture enough terminal output for the existing
AGY quota parser.

## Command Dispatch

After readiness:

```bash
tmux send-keys -t <session> '/usage' Enter
```

Then wait:

```text
AI_MAN_QUOTA_POST_COMMAND_SECONDS
```

Use the AGY default post-command wait unless overridden.

## Capture

Use:

```bash
tmux capture-pane -pt <session> -S -200
```

or an equivalent sufficiently large scrollback window.

The captured pane should include:

- account line
- current model
- visible model quota percentages
- refresh/reset text
- warning text, if present

## Overlay Handling

If `/usage` opens an overlay or scrollable panel, capture it before closing.
Optionally send `Escape` after capture to return AGY to the prompt:

```bash
tmux send-keys -t <session> Escape
```

This should be used only after output capture, not before parsing.

## Parser Integration

Reuse current:

```text
parse_agy_quota()
parse_quota()
```

Do not add tmux-specific parsing if normalized screen output already matches the
existing parser contract.

## Failure Handling

If `/usage` does not produce quota output:

- keep session alive for retry if prompt remains usable;
- return `parser_miss` with diagnostic output;
- invalidate after existing parser miss threshold;
- invalidate immediately only for dead session, process exit, timeout, or
  clearly corrupt terminal state.

## Risks

- Capturing too little scrollback can miss quota lines.
- Capturing too much can include stale prior quota screens. Command dispatch
  should ideally clear or delimit output before sending `/usage`.
