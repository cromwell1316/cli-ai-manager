# H_01 Phase 01 Import Profile Inventory

Owner: cli-profile-manager
Source of Truth: management/horizons/H42_Operations_Lazy_Import_Slimming/README.md
Lifecycle: living
Document Class: horizon-phase

Status: completed.

## Objective

Identify operation imports that materially affect cold startup.

## Deliverables

- Import-time profile for `profile_manager`.
- List of operation dependencies by command path.
- Candidate imports with measured cost and risk.
- Decision list for imports intentionally left unchanged.

## Implementation Notes

- Prefer measurement over broad style cleanup.
- Avoid moving imports that are needed by most commands.
- Track circular import risk before editing.

## Inventory

| Dependency | Top-level cost/risk | Command path | Decision |
| --- | --- | --- | --- |
| `audit` | Pulls audit storage/path helpers | audit operations only | Lazy import |
| `process_policy` | Pulls subprocess/backend probing helpers | launch preparation only | Lazy import |
| `runtime_service` | Pulls socket/service helpers | service operations only | Lazy import |
| `sync` | Pulls credential sync helpers | sync operations only | Lazy import |
| `config` | Pulls config registry and process policy | config operations only | Lazy import |
| AGY/Codex/Claude credential modules | Needed only while inspecting or moving credentials | status/import/export paths | Lazy import |
| `credentials.common` | Needed only for credential file writes | import/export paths | Lazy import |
| `shutil` | Needed only for copy/remove helpers | import/export/clear paths | Lazy import |
| `dataclasses` | Import-time overhead for simple DTOs | `operations` import itself | Removed in favor of local classes |
| `metadata` | Needed by `CommandSnapshot` and common operations | common operation paths | Left top-level |
| `paths` | Needed by profile indexing and common path helpers | common operation paths | Left top-level |

## Risk Notes

- Public class names `OperationResult`, `FileFact`, and `ProfileFact` were kept.
- No payload keys or operation result statuses were changed.
- Deferred modules are imported through small cached accessors to avoid repeated
  import lookups and circular import surprises.
