# setvane-scan — Authority

**Setvane Governance V1**
**Inherits: setvane-ecosystem-governance/profiles/scan.md**

## Authority

```
SCAN = OBSERVE + INSPECT + ANALYZE + REPORT
```

This is the complete and bounded authority of setvane-scan.

## Forbidden Authority

The following are explicitly outside setvane-scan's V1 authority.
They MUST NOT be performed even when presented with a Gate `ALLOW`:

- APPLY (any configuration)
- EXECUTE (any privileged action)
- WRITE (any system state)
- DELETE (any artifact or state)
- INSTALL (any package or artifact)
- RESTART (any service or process)
- REMEDIATE (any finding)

## Evidence Invariant

```
FINDING != REMEDIATION AUTHORITY
SCAN RESULT != PERMISSION TO CHANGE SYSTEM
```

An EvidenceEnvelope produced by setvane-scan:
- Is informational evidence
- Does NOT grant permission to execute any action
- MUST NOT contain `authorization=true`, `approved=true`, or `allow=true`

## Future Remediation

A PolicyDecision does not grant capabilities absent from the active repository profile.

If remediation capability is ever added to setvane-scan:
- It MUST be granted by an updated `setvane-ecosystem-governance/profiles/scan.md`
- It MUST require a matching Gate PolicyDecision for each privileged action
- It MUST NOT be self-authorized
- It MUST follow the full governed lifecycle
