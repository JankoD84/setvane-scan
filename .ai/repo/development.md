# setvane-scan — Development

**Setvane Governance V1**

## Development Workflow

### Implementation Tasks

All implementation tasks MUST:
1. Carry a valid Linear task ID
2. Declare expected worktree, branch, and base SHA or base ref
3. Pass pre-mutation checklist (see `.ai/process/implementation.md`)
4. Leave changes uncommitted for review

### Validation Commands

Run after any implementation:

```bash
git --no-optional-locks status --short --branch
git diff --check
```

If a test suite or linter exists in this repository, run it and report results.

### Branch Convention

Follow repository branching conventions.
Do NOT auto-switch to a different branch to satisfy task expectations.

### Scan Execution

Scan execution is a runtime operation, not a code operation.
Scan runs MUST NOT be triggered by AI agents without explicit human authorization.

Evidence produced by scan runs flows through EvidenceEnvelope to authorized consumers.
Evidence MUST NOT be committed to this repository.

### Future Skills

When implemented, per-repo scan skills will be added to `.agents/skills/`:
- `run-scan`
- `normalize-findings`
- `produce-evidence-report`
