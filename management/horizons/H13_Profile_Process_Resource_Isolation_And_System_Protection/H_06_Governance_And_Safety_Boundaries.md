# H_06 Governance And Safety Boundaries

Owner: cli-profile-manager
Source of Truth: management/horizons/H13_Profile_Process_Resource_Isolation_And_System_Protection/README.md
Lifecycle: living
Document Class: governance

Status: planned.

## Boundaries

- Do not add broad privileged operations.
- Do not require root access.
- Do not use destructive process cleanup outside known child process groups.
- Do not log command environments with token values.
- Do not make quota refresh more important than foreground user interaction.
- Treat resource limits as protection, not as a replacement for correct process
  lifecycle management.
