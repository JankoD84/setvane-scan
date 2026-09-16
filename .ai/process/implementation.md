# setvane-scan — Implementation Mode

**Setvane Governance V1**
**Inherits: setvane-ecosystem-governance/.ai/process/implementation.md**

## MODE=IMPLEMENTATION in setvane-scan

All canonical implementation rules apply. This file adds scan-specific constraints.

## Required Envelope Fields

```
TASK_ID:             # Linear task ID
MODE:                IMPLEMENTATION
REPOSITORY:          setvane-scan
EXPECTED_WORKTREE:   # expected Git worktree root
EXPECTED_BRANCH:     # e.g., main
BASE_SHA:            # expected HEAD SHA; use BASE_REF instead when appropriate
BASE_REF:            # explicit base ref; one of BASE_SHA or BASE_REF is required
SCOPE:               # specific files or subsystems being changed
OUT_OF_SCOPE:        # explicitly excluded
ALLOWED_MUTATIONS:   # specific changes permitted
VALIDATION:          # at minimum: git diff --check
PROTECTED_OPERATIONS: # default: all (merge, rebase, etc.)
```

## Pre-Mutation Checklist

Before any file mutation:

1. Actual repository identity and repository root match setvane-scan?
2. Actual Git worktree root matches EXPECTED_WORKTREE?
3. On expected branch?
4. HEAD matches BASE_SHA or BASE_REF?
5. No unexpected dirty state?
6. Valid Linear task ID present?
7. Mutations within SCOPE?
8. No forbidden remediation logic being added?

If any check fails → `SAFE_TO_EDIT=NO` → STOP + REPORT.
Do not auto-switch repositories, branches, or worktrees.

## Scan-Specific Constraints

An implementation task in setvane-scan MUST NOT:

- Add write or remediation logic under the V1 Scan profile
- Add credential storage to tracked files
- Expand authority beyond OBSERVE + INSPECT + ANALYZE + REPORT
- Commit scan findings to the repository

## Validation

```bash
git --no-optional-locks status --short --branch
git diff --check
```

If tests exist:
```bash
# run repository test suite
```

## Post-Mutation

Leave changes uncommitted. Report changed files and risk.
Do not push without explicit human authorization.
