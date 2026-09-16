# setvane-scan — Review Mode

**Setvane Governance V1**
**Inherits: setvane-ecosystem-governance/.ai/process/review.md**

## MODE=REVIEW in setvane-scan

Review mode is read-only. No file mutations.

### Scan-Specific Review Scope

In addition to standard governance review, review mode in setvane-scan MAY include:

- Reviewing scan configuration files (read-only)
- Reviewing evidence schema definitions
- Reviewing test coverage for scan logic
- Reviewing public disclosure compliance

### What Review Mode MUST NOT Do

- Trigger a live scan against target systems
- Commit or push any file
- Modify scan credentials or scope configuration
- Access target system data directly

### Scan Authority Boundary Check

During review, verify:

- No write/apply/execute authority is present in governance files
- EvidenceEnvelope schema does not contain authorization fields
- Public disclosure rules are respected

See canonical review skill: `setvane-ecosystem-governance/.agents/skills/governance-review.md`
