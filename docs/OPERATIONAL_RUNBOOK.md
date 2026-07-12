# Operational Runbook

This runbook is the repository-native guide for installing, verifying, using,
syncing, recovering, and troubleshooting `ai-man` on WSL/Linux and native
Windows.

## Quickstart

WSL/Linux:

```bash
cd /home/olivercromwell/projects/shared/cli-profile-manager
chmod +x install.sh
./install.sh
./scripts/verify_install.sh
ai-man diagnostics --json
```

Native Windows PowerShell:

```powershell
cd C:\path\to\cli-profile-manager
.\install-windows.ps1
.\scripts\verify_install_windows.ps1
ai-man diagnostics --json
```

Use temporary paths when validating without touching user `Path`:

```powershell
.\install-windows.ps1 `
  -BinDir "$env:TEMP\ai-man-bin" `
  -AgyHome "$env:TEMP\agy-homes" `
  -NoPathUpdate
.\scripts\verify_install_windows.ps1 `
  -BinDir "$env:TEMP\ai-man-bin" `
  -AgyHome "$env:TEMP\agy-homes" `
  -SkipPathCheck `
  -SkipCredentialCheck
```

## Install, Update, Verify, Roll Back

WSL/Linux install creates `ai-man`, `profile-man`, and `pman` symlinks in
`~/.local/bin` by default. Set `AI_MAN_INSTALL_BIN_DIR=/path/to/bin` to use a
different directory.

```bash
./install.sh
./scripts/verify_install.sh
```

WSL/Linux update is idempotent:

```bash
git pull
./install.sh
./scripts/verify_install.sh
```

WSL/Linux rollback removes only generated aliases:

```bash
rm -f ~/.local/bin/ai-man ~/.local/bin/profile-man ~/.local/bin/pman
```

Native Windows install creates PowerShell and CMD shims in
`%LOCALAPPDATA%\Programs\ai-man\bin` by default and installs the managed AGY
Credential Manager helper into `%USERPROFILE%\agy-homes`.

```powershell
.\install-windows.ps1
.\scripts\verify_install_windows.ps1
```

Native Windows update is idempotent:

```powershell
git pull
.\install-windows.ps1
.\scripts\verify_install_windows.ps1
```

If the verifier reports stale PowerShell profile functions, aliases, or missing
dot-sourced files, inspect the proposed repair first:

```powershell
.\scripts\repair_windows_profile.ps1
```

Apply cleanup only when the dry-run output matches the stale entries you want to
disable. The repair command writes a profile backup before commenting any
conflicting lines:

```powershell
.\scripts\repair_windows_profile.ps1 -Apply -ConfirmCleanup
```

To roll back a profile cleanup, copy the generated
`*.ai-man-backup-YYYYMMDD-HHMMSS` file back over the PowerShell profile path
shown by the repair command.

Native Windows rollback removes generated shims and the managed helper:

```powershell
Remove-Item -LiteralPath "$env:LOCALAPPDATA\Programs\ai-man\bin\ai-man.ps1" -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath "$env:LOCALAPPDATA\Programs\ai-man\bin\ai-man.cmd" -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath "$env:LOCALAPPDATA\Programs\ai-man\bin\profile-man.ps1" -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath "$env:LOCALAPPDATA\Programs\ai-man\bin\profile-man.cmd" -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath "$env:LOCALAPPDATA\Programs\ai-man\bin\pman.ps1" -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath "$env:LOCALAPPDATA\Programs\ai-man\bin\pman.cmd" -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath "$env:USERPROFILE\agy-homes\ai-man-agy-credential.ps1" -Force -ErrorAction SilentlyContinue
```

If PowerShell blocks scripts:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

For one current shell only, especially when running from a WSL UNC path:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

If `ai-man` is not found after Windows install, open a new PowerShell window or
run the verifier with `-SkipPathCheck` when using temporary directories.

## Profile Roots And Credential Authority

Default managed profile roots:

```text
agy    WSL/Linux: ~/agy-homes/pN/.gemini/oauth_creds.json
agy    Windows:   %USERPROFILE%\agy-homes\cred-pN.json
codex  both:      codex-homes/pN/auth.json
claude both:      claude-homes/pN/.credentials.json
```

AGY has different authority on each platform:

```text
WSL OAuth file       -> ~/agy-homes/pN/.gemini/oauth_creds.json
Windows backup file  -> %USERPROFILE%\agy-homes\cred-pN.json
Windows live slot    -> Credential Manager target gemini:antigravity
```

`sync`, `import`, `export`, and `agy-credential restore` convert or copy managed
backup files. They do not print OAuth token blobs. Native Windows `launch` and
`login` use the managed helper to write one selected `cred-pN.json` backup into
the shared live Credential Manager slot before AGY runs.

## First Login And Daily Operation

Create first profiles:

```bash
ai-man login agy p1
ai-man login codex p1
ai-man login claude p1
```

Create additional AGY profiles:

```bash
ai-man login agy p2
ai-man login agy p3
```

Launch profiles:

```bash
ai-man launch agy p1
ai-man launch codex p1
ai-man launch claude p1
```

Inspect status and quota:

```bash
ai-man list agy --json
ai-man status agy p1 --quota --json
ai-man quota agy p1 --json
ai-man diagnostics agy --json --show-accounts
```

Import and export credentials:

```bash
ai-man import agy /mnt/c/Users/Oliver/agy-homes/cred-p1.json p1 --dry-run --json
ai-man import agy /mnt/c/Users/Oliver/agy-homes/cred-p1.json p1
ai-man export agy p1 --to /mnt/c/Users/Oliver/Downloads --dry-run --json
ai-man export agy p1 --to /mnt/c/Users/Oliver/Downloads
```

Use placeholder paths and profile numbers for your own environment. Do not paste
raw OAuth tokens into commands, issues, logs, or screenshots.

## Sync Between WSL And Windows

Read sync direction as "copy from this side to the other side".

WSL to Windows:

```bash
ai-man sync --from wsl --mode soft --dry-run --json
ai-man sync --from wsl --mode soft
```

Windows to WSL:

```bash
ai-man sync --from windows --mode soft --dry-run --json
ai-man sync --from windows --mode soft
```

Hard sync can delete destination managed files and requires confirmation:

```bash
ai-man sync --from wsl --mode hard --dry-run --json
ai-man sync --from wsl --mode hard --yes
```

Use explicit roots for testing or unusual layouts:

```bash
AI_MAN_WSL_HOME=/tmp/wsl AI_MAN_WINDOWS_HOME=/tmp/windows \
  ai-man sync --from wsl --mode soft --dry-run --json
```

`sync --json` reports `sync_roots`, copied files, skipped files, converted AGY
credentials, invalid backups, and hard-delete preflight paths.

## Credential Recovery

Inspect managed AGY backups:

```bash
ai-man agy-credential whoami --json
ai-man diagnostics agy --json --show-accounts
```

Restore an external Windows AGY backup into a managed profile:

```bash
ai-man agy-credential restore /path/to/cred-backup.json p2 --dry-run --json
ai-man agy-credential restore /path/to/cred-backup.json p2 --yes
```

On native Windows, also restore the live Credential Manager slot:

```powershell
ai-man agy-credential restore .\cred-backup.json p2 --set-live --dry-run --json
ai-man agy-credential restore .\cred-backup.json p2 --set-live --yes
ai-man agy-credential set p2 --dry-run --json
ai-man agy-credential set p2 --yes
ai-man agy-credential save p2 --yes
ai-man agy-credential clear --yes
```

Recovery rules:

- Run `--dry-run --json` before any mutation.
- Mutating recovery actions require `--yes`.
- Invalid backups fail before writing `cred-pN.json`.
- Output includes paths, validity, account metadata, and timestamps, not token
  blobs.
- If a live Windows slot is wrong, close active AGY sessions, run
  `ai-man agy-credential set pN --yes`, then run diagnostics.

## Diagnostics And Troubleshooting

General diagnostics:

```bash
ai-man diagnostics --json
ai-man diagnostics agy --json --show-accounts
ai-man config show --json
ai-man service status --json
ai-man audit list --json
```

Install verification:

```bash
./scripts/verify_install.sh
```

```powershell
.\scripts\verify_install_windows.ps1
.\scripts\repair_windows_profile.ps1
.\scripts\windows_ci_smoke.ps1 -BinDir "$env:TEMP\ai-man-bin" -AgyHome "$env:TEMP\agy-homes"
```

Live AGY quota validation from WSL/Linux:

```bash
python3 scripts/validate_agy_quota_live.py --dry-run
python3 scripts/validate_agy_quota_live.py --concurrency 2 --timeout 60
```

Common failures:

- Missing CLI: install the native `agy`, `codex`, or `claude` command and open a
  new shell.
- Stale Windows helper: rerun `.\install-windows.ps1`.
- Stale Windows PATH: open a new PowerShell window or use `-SkipPathCheck` for
  temporary validation.
- Stale Windows PowerShell profile: run
  `.\scripts\repair_windows_profile.ps1`, then apply
  `.\scripts\repair_windows_profile.ps1 -Apply -ConfirmCleanup` after reviewing
  the dry-run output.
- Logged out profile: run `ai-man login <tool> pN` or import a valid credential.
- Invalid AGY backup: restore from another `cred-pN.json` or run native login
  again.

## Known Limitations

- Native Windows AGY has one shared Credential Manager target per Windows user:
  `gemini:antigravity`.
- Same-user parallel native Windows AGY sessions are not true isolation.
  `ai-man` serializes live slot operations with a named mutex and documents
  separate Windows users as the isolation boundary.
- Native Windows AGY quota uses a prompt/helper path and can be slower than
  WSL/Linux terminal quota probing.
- CI smoke checks are token-safe and do not prove live account quota behavior.
- Sync only manages known profile credential files and manager metadata; it does
  not copy caches, logs, virtual environments, or unmanaged runtime artifacts.

## Evidence And Governance

Run local governance and smoke checks:

```bash
python3 scripts/horizon_governance.py --json
python3 profile_manager.py --help
python3 profile_manager.py config show --json
python3 -m pytest
```

Key implementation horizons:

- `management/horizons/H45_Windows_AGY_Quota_Backend`
- `management/horizons/H46_Windows_Interactive_Surface`
- `management/horizons/H47_Windows_Install_Verification`
- `management/horizons/H48_Cross_Platform_Sync_E2E`
- `management/horizons/H49_AGY_Concurrent_Session_Safety`
- `management/horizons/H50_Native_Windows_CI_Smoke_Matrix`
- `management/horizons/H51_Credential_Recovery_And_Backup_UX`
