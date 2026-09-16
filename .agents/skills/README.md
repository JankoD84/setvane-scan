# setvane-scan — Skills

Skills define workflows within established authority. Skills do NOT grant permission.

## Available Skills

None implemented yet. Planned:

| Skill | Purpose |
|-------|---------|
| run-scan | Procedure for triggering a governed scan run |
| normalize-findings | Normalize raw scan output into EvidenceEnvelope format |
| produce-evidence-report | Produce a structured evidence report from scan results |

These will be added as `.md` files in this directory when implemented.

## Shared Skills

The following shared governance skills are available from the canonical governance repository:

| Skill | Source |
|-------|--------|
| governance-review | `setvane-ecosystem-governance/.agents/skills/governance-review.md` |
| governance-implementation | `setvane-ecosystem-governance/.agents/skills/governance-implementation.md` |
| cross-repo-change | `setvane-ecosystem-governance/.agents/skills/cross-repo-change.md` |

## Skill Contract

A skill MUST NOT:
- Grant permission to execute privileged actions
- Override governance invariants
- Substitute for a Gate PolicyDecision

A skill IS a how-to procedure within already-established authority.
