# H_02 Phase 02 Platform Path Normalization

Owner: cli-profile-manager
Source of Truth: management/horizons/H37_Windows_WSL_Path_Parity_After_Import/README.md
Lifecycle: living
Document Class: phase

Status: implemented.

## Objective

Keep import path normalization platform-correct.

## Required Behavior

- On WSL/POSIX, pasted Windows paths like `C:\Users\Oliver\...` become
  `/mnt/c/Users/Oliver/...`.
- On native Windows, `C:\Users\Oliver\...` remains a native Windows path.
- Directory imports for Codex and Claude still append their expected credential
  filenames.
- AGY credential conversion remains based on `cred-pN.json` backups and
  `.gemini/oauth_creds.json` WSL profile files.

## Risks

The dangerous regression is silently rewriting a valid native Windows path into
an unusable WSL mount path. Tests must cover both platform branches.
