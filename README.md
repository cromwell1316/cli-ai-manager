# Unified CLI Profile Manager for WSL

Keyboard-first command-line manager for isolated **Antigravity CLI** (`agy`),
**OpenAI Codex CLI** (`codex`), and **Anthropic Claude CLI** (`claude`)
profiles under WSL/Linux.

The supported local interface is `profile_manager.py`, installed as `ai-man`,
`profile-man`, and `pman`. Legacy alternate entrypoints have been removed; use
`ai-man` for all profile operations.

## Features

- Manage `agy`, `codex`, and `claude` profiles from one terminal command.
- Launch each CLI with isolated profile environment variables.
- Add OAuth profiles through the native CLI login flow.
- Import credentials from Windows profile backups.
- Export credentials back to Windows-friendly files.
- Label profiles for easier identification.
- View profile status and token presence.
- Probe per-profile quota through the native agent CLI.
- Sync profile folders between WSL and Windows.

## Installation

Run the installer from this directory:

```bash
chmod +x install.sh
./install.sh
```

The installer creates these symlinks in `~/.local/bin`:

```text
ai-man      -> profile_manager.py
profile-man -> profile_manager.py
pman        -> profile_manager.py
```

Ensure `~/.local/bin` is in your shell `PATH`, then run:

```bash
ai-man
```

## Direct Commands

Use direct commands for the fastest path and for scripts:

```bash
ai-man list agy
ai-man list codex --json
ai-man status claude p1
ai-man status codex p1 --quota --json
ai-man quota codex p1 --json
ai-man launch agy p2 -- --help
ai-man login codex p3
ai-man import agy /mnt/c/Users/Oliver/agy-homes/cred-p1.json p1
ai-man export codex p1 --to /mnt/c/Users/Oliver/Downloads
ai-man label claude p1 work
ai-man clear agy p4 --yes
ai-man sync --from wsl --mode soft
```

Command grammar:

```text
ai-man list <tool> [--json] [--quota] [--timeout seconds]
ai-man status <tool> <profile> [--json] [--quota] [--timeout seconds]
ai-man quota <tool> <profile> [--json] [--timeout seconds]
ai-man diagnostics [tool] [--json] [--show-accounts]
ai-man launch <tool> <profile> [-- args...]
ai-man login <tool> [profile]
ai-man import <tool> <path> [profile]
ai-man export <tool> <profile> [--to path]
ai-man label <tool> <profile> <label>
ai-man clear <tool> <profile> --yes
ai-man sync [--from wsl|windows] [--mode soft|hard] [--dry-run] [--yes]
```

Supported tools are `agy`, `codex`, and `claude`. Profiles accept `pN` or `N`.
When a command creates or imports into a profile and no profile is supplied, it
uses the first free positive profile number.

Exit codes:

```text
0 success
2 invalid command or profile
3 missing file, tool executable, source, or destination
4 profile has no token for a token-required operation
5 runtime failure
```

`clear` refuses to delete a profile unless `--yes` is supplied.

Quota probing uses a PTY and the native CLI for each profile, because these
agents render usage data only in terminal mode. The default quota commands are
`/usage` for `agy`, `/status` for `codex`, and `/usage` for `claude`; override
them with `AI_MAN_AGY_QUOTA_COMMAND`, `AI_MAN_CODEX_QUOTA_COMMAND`, or
`AI_MAN_CLAUDE_QUOTA_COMMAND` if a local CLI version changes its command. If a
profile is logged out, the quota payload reports `auth_required` or `no_token`
instead of returning partial numbers.

Interactive `ai-man` screens load quota automatically in the background for
active profiles and cache it for the current session. Fresh quota data is shown
in green; cached data older than five minutes is shown in red. Set
`AI_MAN_INTERACTIVE_QUOTA=0` to disable automatic probing, or
`AI_MAN_INTERACTIVE_QUOTA_TIMEOUT=<seconds>` to change the generic per-profile
timeout. AGY supports `AI_MAN_INTERACTIVE_AGY_QUOTA_TIMEOUT=<seconds>` and
`AI_MAN_INTERACTIVE_AGY_QUOTA_CONCURRENCY=<workers>` for its slower interactive
quota probes. Set `AI_MAN_QUOTA_STARTUP_SECONDS=<seconds>` if a native CLI needs
more startup time before slash commands are accepted.

AGY status uses separate quota columns. `FM`, `FH`, and `FL` are Gemini Flash
medium/high/low; `PL` and `PH` are Gemini Pro low/high; `CS` and `CO` are Claude
Sonnet/Opus. `...` means a quota probe is queued or running, `~` marks a stale
value being refreshed, and `!` marks a retryable failure whose details are
available from JSON commands or diagnostics.

Diagnostics are safe by default:

```bash
ai-man diagnostics --json
ai-man doctor agy --json
```

The diagnostics payload reports configured profile roots, CLI availability,
quota scheduler/cache state, and persistent quota sessions. Account identifiers
are redacted unless `--show-accounts` is supplied; token-like values are always
redacted.

Optional live AGY validation is available for local troubleshooting:

```bash
python3 scripts/validate_agy_quota_live.py --dry-run
python3 scripts/validate_agy_quota_live.py --concurrency 2 --timeout 60
```

## Interactive Selector

Launching `ai-man` opens the keyboard selector:

```text
[1] Antigravity CLI (agy)
[2] OpenAI Codex CLI
[3] Anthropic Claude CLI
[4] Sync Profiles (WSL <-> Windows)
[x] Exit
```

Keys:

```text
digits  select visible item
arrows  move selection
Enter   confirm or launch
a       add/login
i       import
e       export
l       label
s       status
c       clear
q/Esc   back or exit
```

Inside each tool manager you can:

- launch an existing profile;
- add a new profile through OAuth;
- import credentials from Windows automatically or manually;
- export a credential to Windows;
- clear a profile after explicit confirmation;
- set a profile label;
- inspect detailed account status.

## Profile Isolation

The manager uses separate profile directories:

```text
~/agy-homes/pN
~/codex-homes/pN
~/claude-homes/pN
```

It launches tools with the corresponding environment override:

```text
agy    -> HOME
codex  -> CODEX_HOME
claude -> CLAUDE_CONFIG_DIR
```

For `agy`, Windows and WSL use different authoritative credential files:

```text
WSL profile token      -> ~/agy-homes/pN/.gemini/oauth_creds.json
Windows token backup  -> %USERPROFILE%\agy-homes\cred-pN.json
Windows live slot     -> Credential Manager target gemini:antigravity
```

Importing an `agy` Windows `cred-pN.json` decodes `BlobBase64` and writes the
WSL OAuth JSON file. Exporting an `agy` WSL profile wraps
`.gemini/oauth_creds.json` into a Windows backup JSON with target
`gemini:antigravity`. Sync performs the same conversion in the selected
direction; it does not mutate the live Windows Credential Manager slot during
dry-run validation.

Credential formats and Windows/WSL parity are tracked in:

```text
management/horizons/H03_Windows_WSL_Profile_Parity_And_Verification
```

## Verification

Run the command-surface checks after changing supported runtime files:

```bash
python3 -m py_compile profile_manager.py
python3 profile_manager.py --help
python3 profile_manager.py list agy --json
python3 profile_manager.py list codex --json
python3 profile_manager.py list claude --json
./scripts/verify_no_tui_surface.sh
```

## Project Structure

```text
cli-profile-manager/
├── profile_manager.py
├── install.sh
├── scripts/
│   └── verify_no_tui_surface.sh
├── management/
│   └── horizons/
└── README.md
```
