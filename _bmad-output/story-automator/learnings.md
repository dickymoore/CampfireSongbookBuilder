# Story Automator Learnings

## 2026-05-23

- Manual in-controller completion was required repeatedly when spawned story-automator
  worker steps stalled in analysis-only loops instead of crossing file-write
  boundaries.
- Keeping story-scoped commits separate from orchestration bookkeeping made it
  practical to advance the automator safely in a dirty worktree.
- The remediation stack benefited from incremental stories: backup-first state,
  bounded execution, post-remediation re-evaluation, and retry-limit enforcement
  landed cleanly as separate contracts with focused regression coverage.

