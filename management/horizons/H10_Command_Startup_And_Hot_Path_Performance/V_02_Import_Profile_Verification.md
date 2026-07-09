# V_02 Import Profile Verification

Owner: cli-profile-manager
Source of Truth: management/horizons/H10_Command_Startup_And_Hot_Path_Performance/README.md
Lifecycle: living
Document Class: validation

Status: implemented.

## Checks

- `python3 -X importtime profile_manager.py --help` evidence is captured.
- Heavy imports are moved behind command handlers where safe.
- Help/config paths avoid quota PTY imports.
- Compatibility imports remain covered by tests.

## Evidence

- `python3 -X importtime profile_manager.py --help` was captured before and
  after lazy import changes in `/tmp/h10-before-importtime.log` and
  `/tmp/h10-final3-importtime.log`.
- Final import-time evidence for `--help` no longer includes
  `cli_profile_manager.quota`, `cli_profile_manager.diagnostics`,
  `cli_profile_manager.sync`, or credential modules.
- Top-level CLI imports for quota runners, diagnostics payloads, sync helpers,
  credential helpers, logging, subprocess, shlex, and shutil are now lazy.
- Compatibility names remain available through wrapper functions and are covered
  by `python3 -m pytest -q`.
- `test_help_and_config_show_do_not_import_quota_module` verifies help/config
  paths avoid quota and interactive imports.
