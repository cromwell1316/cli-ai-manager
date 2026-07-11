# V_01 Acceptance Matrix

Owner: cli-profile-manager
Source of Truth: management/horizons/H26_Startup_And_Import_Slimming/README.md
Lifecycle: living
Document Class: validation

Status: implemented.

| Area | Acceptance | Evidence |
| --- | --- | --- |
| Help path | `--help` avoids quota, interactive, and audit initialization without affecting passthrough `-h` | Importtime and targeted test |
| Config path | `config show` avoids quota and interactive modules | Targeted test |
| Behavior | Commands, flags, output, and exit codes remain stable | Targeted tests |
| Performance | Cold common commands improve or remain within budget | Runtime benchmark |
