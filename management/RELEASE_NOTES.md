# Release Notes

## Completed Horizons

### H23 AGY Quota PTY Controlling Terminal And Readiness Fix

- Fixed AGY quota probes by launching native CLIs with a real controlling
  terminal and waiting for AGY readiness before sending `/usage`.
- Added AGY quota diagnostics for TTY startup failures, auth/account failures,
  resource exhaustion, parser misses, and local quota process memory limits.
- Added fake CLI regression coverage for `/dev/tty` and readiness-gated slash
  command delivery.
- Tuned AGY quota startup defaults for current WSL behavior, including a 6144 MB
  quota-process memory cap.

### H21 Documentation Governance And Horizon Evidence Automation

- Added local horizon governance validation for required files, source-of-truth
  links, status vocabulary, acceptance matrices, and validation commands.
- Added sanitized horizon evidence collection from `V_00_Validation_Plan.md`
  command blocks with optional `V_99_Automated_Evidence.md` output.
- Documented README usage for governance checks and evidence capture.
