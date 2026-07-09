# V_01 Filesystem Budget Verification

Owner: cli-profile-manager
Source of Truth: management/horizons/H11_Status_IO_Indexing_And_Command_Cache_Performance/README.md
Lifecycle: living
Document Class: validation

Status: implemented.

## Checks

- Profile root scans are counted.
- Metadata reads are counted.
- Credential status reads are counted.
- AGY account log scans are counted.
- Budgets fail on repeated scans in one command execution.

## Evidence

- `tests/test_profile_manager.py::test_command_snapshot_reuses_profile_discovery_and_status`
  fails if a command snapshot repeats occupied-profile discovery for one tool.
- Full validation: `python3 -m pytest -q` passed with 76 tests.
