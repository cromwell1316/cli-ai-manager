# V_01 Acceptance Matrix

Owner: cli-profile-manager
Source of Truth: management/horizons/H40_Cached_Command_Parser_For_Runtime_Service/README.md
Lifecycle: living
Document Class: validation

Status: planned.

| Area | Acceptance | Evidence |
| --- | --- | --- |
| Reuse | Runtime-service commands reuse one parser instance | Runtime parser accessor test |
| Isolation | Repeated parses do not leak namespace state | Cross-command parse tests |
| Compatibility | Public command grammar and errors remain stable | Existing parser tests |
| Performance | In-process command execution gets cheaper | Command benchmark output |
