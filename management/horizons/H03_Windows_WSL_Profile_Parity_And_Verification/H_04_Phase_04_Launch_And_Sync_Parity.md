# H_04 Phase 04 Launch And Sync Parity

Owner: cli-profile-manager
Source of Truth: management/horizons/H03_Windows_WSL_Profile_Parity_And_Verification/README.md
Lifecycle: living
Document Class: phase

Status: planned.

## Scope

Ensure launch and sync use the platform model instead of copying files blindly.

## Required Behavior

- Windows launch/login uses `agy-multiaccount.ps1` or equivalent Credential
  Manager API calls.
- WSL launch/login only sets isolated `HOME`.
- WSL -> Windows sync generates or refreshes `cred-pN.json`.
- Windows -> WSL sync generates or refreshes `.gemini/oauth_creds.json`.
- Hard sync requires explicit confirmation and a preflight summary of files that
  would be removed.

## Phase Exit

The same profile number has consistent status after sync in both environments.
