# H_02 Phase 02 Runtime Service Parser Cache

Owner: cli-profile-manager
Source of Truth: management/horizons/H40_Cached_Command_Parser_For_Runtime_Service/README.md
Lifecycle: living
Document Class: horizon-phase

Status: completed.

## Objective

Add and validate a cached parser accessor for runtime-service command handling.

## Deliverables

- Runtime-service parser accessor.
- Fresh parser factory kept for tests and one-shot CLI startup.
- Coverage for command aliases, errors, and repeated parses.
- Benchmark evidence for in-process command execution.

## Implementation Notes

- Scope the cache to the current process.
- Keep parser construction single-thread safe for expected runtime-service use.
- Avoid broad command dispatch refactors.

## Result

Added `runtime_command_parser()` and `reset_runtime_command_parser_cache()`.
In-process command execution uses the cached accessor while public parser
creation through `build_parser()` remains unchanged.
