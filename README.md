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

## Usage

Launching `ai-man` opens the keyboard selector:

```text
[1] Antigravity CLI (agy)
[2] OpenAI Codex CLI
[3] Anthropic Claude CLI
[4] Sync Profiles (WSL <-> Windows)
[x] Exit
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

Credential formats and Windows/WSL parity are tracked in:

```text
management/horizons/H03_Windows_WSL_Profile_Parity_And_Verification
```

## Verification

Run the H01 checks after changing supported runtime files:

```bash
python3 -m py_compile profile_manager.py
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
