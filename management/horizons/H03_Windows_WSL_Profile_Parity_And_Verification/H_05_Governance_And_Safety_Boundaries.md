# H_05 Governance And Safety Boundaries

Owner: cli-profile-manager
Source of Truth: management/horizons/H03_Windows_WSL_Profile_Parity_And_Verification/README.md
Lifecycle: living
Document Class: governance

Status: implemented.

## Secret Handling

Real `cred-pN.json`, `oauth_creds.json`, `auth.json`, and `.credentials.json`
files are secrets. Fixtures must use synthetic tokens.

## Windows Credential Manager Boundary

Validation must not mutate the live `gemini:antigravity` slot unless the user
explicitly runs an integration test.

## Parallelism Boundary

The project may support staggered Windows agy launch. It must not claim true
parallel account isolation while the shared Credential Manager slot remains.
