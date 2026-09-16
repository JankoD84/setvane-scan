# AGENTS.md — setvane-scan

## Repository Identity

| Field | Value |
|-------|-------|
| Repository | setvane-scan |
| Profile | scan |
| Visibility | **Public** |
| Governance version | Setvane Governance V1 |
| Canonical governance | setvane-ecosystem-governance |
| Linear | DUL-736 |

## Authority Boundary

```
SCAN = OBSERVE + INSPECT + ANALYZE + REPORT
```

This repository is **READ-ONLY** by default.

### Authorized

`OBSERVE` `INSPECT` `ANALYZE` `REPORT`

### Forbidden in V1 (a Gate ALLOW does not expand profile authority)

- System modification of any kind
- Package installation or removal
- Firewall or network modification
- SSH configuration modification
- Service restart or process management
- Docker container mutation
- systemd unit mutation
- File deletion on target systems
- Automatic remediation
- Configuration application

Future remediation requires both a canonical Scan profile revision and a matching
Gate PolicyDecision. A PolicyDecision alone cannot add Scan capabilities.

`FINDING != REMEDIATION AUTHORITY`
`SCAN RESULT != PERMISSION TO CHANGE SYSTEM`

## Cross-Repo Role

setvane-scan is the **authoritative producer** of `EvidenceEnvelope`.

setvane-scan MUST NOT produce ChangeProposals or issue PolicyDecisions.

## Execution Modes

**MODE=REVIEW** — inspect, analyze, report only. No mutations.

**MODE=IMPLEMENTATION** — requires TASK_ID, EXPECTED_WORKTREE, EXPECTED_BRANCH,
BASE_SHA or BASE_REF, and SCOPE.
Run pre-mutation checklist before any file edit.
See `.ai/process/implementation.md`.

## Git Safety

Protected operations require explicit human approval.
Wrong repo/branch/worktree or unexpected dirty state → `SAFE_TO_EDIT=NO` → STOP + REPORT.
See `.ai/repo/security.md`.

## Linear Binding

Every non-trivial implementation MUST carry a valid Linear task ID.
Missing task ID → STOP + REPORT.

## Public Disclosure

This repository is **public**. All committed content MUST comply with public disclosure rules.

MUST NOT expose: secrets, tokens, private keys, internal IPs, hostnames,
customer data, private operational procedures.

## Validation

```bash
git --no-optional-locks status --short --branch
git diff --check
```

See `.ai/process/implementation.md` for full validation suite.

## Canonical Reference

Full governance: `setvane-ecosystem-governance` (canonical governance source)

| Topic | Canonical file |
|-------|---------------|
| Invariants | `setvane-ecosystem-governance/.ai/governance/invariants.md` |
| Authority model | `setvane-ecosystem-governance/.ai/governance/authority-model.md` |
| Git Safety | `setvane-ecosystem-governance/.ai/governance/git-safety.md` |
| Authorization | `setvane-ecosystem-governance/.ai/governance/authorization.md` |
| Public safety | `setvane-ecosystem-governance/.ai/governance/public-repository-safety.md` |
| Scan profile | `setvane-ecosystem-governance/profiles/scan.md` |
| Evidence contract | `setvane-ecosystem-governance/contracts/evidence-contract.md` |
