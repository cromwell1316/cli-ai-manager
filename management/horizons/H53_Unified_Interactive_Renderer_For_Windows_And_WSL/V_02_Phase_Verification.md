# V_02 Phase Verification

Owner: cli-profile-manager
Source of Truth: management/horizons/H53_Unified_Interactive_Renderer_For_Windows_And_WSL/README.md
Lifecycle: living
Document Class: validation

Status: planned.

## Verification Matrix

| Phase | Verification |
| --- | --- |
| Phase 01 | Surface inventory covers WSL and native Windows screens. |
| Phase 02 | Shared descriptors model labels, shortcuts, and action IDs. |
| Phase 03 | Platform adapters render the same semantic actions. |
| Phase 04 | Core workflows route through shared definitions. |
| Phase 05 | Duplicate routing is removed and docs are updated. |

## Commands

```bash
python3 -m pytest tests/test_profile_manager.py -k "interactive or windows_interactive"
python3 scripts/horizon_governance.py --json
python3 -m pytest
```

