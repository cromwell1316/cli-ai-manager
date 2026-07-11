# V_01 Acceptance Matrix

Owner: cli-profile-manager
Source of Truth: management/horizons/H40_Cached_Command_Parser_For_Runtime_Service/README.md
Lifecycle: living
Document Class: validation

Status: completed.

| Area | Acceptance | Evidence |
| --- | --- | --- |
| Reuse | Runtime-service commands reuse one parser instance | `test_runtime_service_execute_argv_uses_cached_parser` and `test_run_cli_default_path_uses_process_local_parser_cache` |
| Isolation | Repeated parses do not leak namespace state | `test_runtime_command_parser_repeated_parses_do_not_leak_state` |
| Compatibility | Public command grammar and errors remain stable | `pytest -q tests/test_profile_manager.py -k "parser or command or runtime"` |
| Performance | In-process command execution gets cheaper | `command-execute` benchmark medians captured in validation plan |
