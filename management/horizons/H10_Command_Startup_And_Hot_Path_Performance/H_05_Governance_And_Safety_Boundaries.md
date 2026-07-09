# H_05 Governance And Safety Boundaries

Owner: cli-profile-manager
Source of Truth: management/horizons/H10_Command_Startup_And_Hot_Path_Performance/README.md
Lifecycle: living
Document Class: governance

Status: implemented.

## Boundaries

- Preserve every public command name, flag, exit code, and JSON field unless a
  later horizon explicitly deprecates it.
- Keep redaction guarantees in diagnostics and config output.
- Do not cache or write sensitive credential contents for performance.
- Do not use live AGY/Codex/Claude CLIs in deterministic perf tests.
- Treat host Python startup cost as an external measurement unless H12 chooses a
  long-lived process model.
