# setvane-scan — Security

**Setvane Governance V1**
**Inherits: setvane-ecosystem-governance/.ai/governance/public-repository-safety.md**

## Public Repository Security

setvane-scan is public. The following MUST NOT appear in any committed file:

- Secrets, API keys, tokens, passwords
- Private keys of any kind
- Internal IP addresses or hostnames
- Private infrastructure topology
- Customer data or customer-identifying information
- Internal incident details
- Unpublished vulnerability details
- Internal operational procedures

Security principles, authority boundaries, and public-safe governance documentation MAY appear.

## Scan Credentials

Credentials used by setvane-scan to access target systems MUST NOT be committed to this repository.
They MUST be injected at runtime through a secret management system.

## Finding Sensitivity

Scan findings may contain sensitive information about target systems.
Findings MUST NOT be committed to this public repository.
Findings MUST be transmitted through the EvidenceEnvelope contract to authorized consumers only.

## Security-Sensitive Changes

Changes to:
- Scan scope or target definitions
- Evidence schema
- Credential handling
- Network access configuration

Require explicit human review before merge.

## Git Safety

Protected operations (merge, rebase, cherry-pick, amend, reset, clean, force push,
branch deletion, stash drop) require explicit human approval.

Wrong repo/branch/worktree or unexpected dirty state:
```
SAFE_TO_EDIT = NO
ACTION = STOP + REPORT
```
