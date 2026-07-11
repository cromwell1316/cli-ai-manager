# H_02 Phase 02 Adaptive Capture And Waiting

Owner: cli-profile-manager
Source of Truth: management/horizons/H29_Quota_Warm_Path_Optimization/README.md
Lifecycle: living
Document Class: horizon-phase

Status: implemented.

## Objective

Replace fixed waiting and broad capture with marker-driven capture where safe.

## Deliverables

- Quota marker polling.
- Short capture on success.
- Long capture on parser miss.
- Warm liveness cache.

## Result

- Tmux warm path polls short captures until parser-recognized quota output is
  visible.
- Parser misses use a longer capture before returning diagnostic output.
- Recent tmux liveness results are cached for a short configurable interval.
- Existing parser-miss invalidation behavior is preserved.
