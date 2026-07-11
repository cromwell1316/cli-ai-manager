# H_01 Phase 01 Service Baseline And Command Eligibility

Owner: cli-profile-manager
Source of Truth: management/horizons/H27_Runtime_Service_Acceleration/README.md
Lifecycle: living
Document Class: horizon-phase

Status: implemented.

## Objective

Measure service-backed commands and confirm which commands are safe to serve.

## Deliverables

- One-shot vs service benchmark.
- Eligible command matrix.
- Mutation invalidation review.
- Service fallback behavior inventory.

## Result

- Service eligibility remains limited to read-only commands.
- `list` and `status` with `--quota` remain excluded from service fast paths.
- Mutating commands continue to notify the runtime service after successful
  mutations.
- Service-backed command output is covered by equivalence tests against one-shot
  execution.
