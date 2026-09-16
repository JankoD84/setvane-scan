#!/usr/bin/env python3
"""Advisory Setvane Governance V1 product projection validator.

CI authority belongs to the immutable canonical reusable workflow. This local validator
provides developer parity checks but cannot authorize compliance.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

SUPPORTED_VERSION = "v1"
CANONICAL_REPOSITORY = "JankoD84/setvane-ecosystem-governance"
CANONICAL_REVISION = "4218a374acf2845b6a2ca89e46d0b11c9266bdee"
LOCK_PATH = Path(".ai/governance.lock")
VALIDATOR_PATH = ".governance/validate.py"
INVENTORY_ROOTS = (Path(".ai"), Path(".agents/skills"), Path(".governance"))
GOVERNED_WORKFLOWS = {"governance-validation.yml"}
EXPECTED_REPOSITORIES = {
    "jankod84/setvane-scan": ("setvane-scan", "scan", "public", True),
    "jankod84/setvane-config": ("setvane-config", "config", "private", False),
    "jankod84/setvane-gate": ("setvane-gate", "gate", "public", True),
}
EXPECTED_LOCK_DIGEST = "c6477239e24a9f67a517ece9edc30b3a02782c670785c0b1e712fb5ffcefd143"
GITHUB_REMOTE_PATTERN = re.compile(
    r"^(?:git@github\.com:|https://github\.com/)([^/]+)/([^/]+?)(?:\.git)?/?$",
    re.IGNORECASE,
)
AUTHORITY_PATTERNS = {
    "scan": (
        re.compile(
            r"(?:scan|setvane-scan)\s+(?:may|can|is authorized to)\s+"
            r"(?:write|apply|execute|remediate)",
            re.I,
        ),
        re.compile(r"\b(?:WRITE|APPLY|EXECUTE|REMEDIATE)\s*=\s*AUTHORIZED\b", re.I),
    ),
    "config": (
        re.compile(r"config\s+(?:may|can|is authorized to)\s+self[- ]?authorize", re.I),
        re.compile(r"self[-_ ]?authorization\s*[:=]\s*(?:true|allowed|authorized)", re.I),
    ),
    "gate": (
        re.compile(
            r"(?:AI|LLM)\s+(?:may|can|is authorized to)\s+"
            r"(?:independently\s+)?issue\s+(?:an\s+)?authoritative\s+`?ALLOW",
            re.I,
        ),
        re.compile(r"REQUIRE_APPROVAL\s+(?:is|=)\s+(?:directly\s+)?executable", re.I),
    ),
}
SKILL_PERMISSION_PATTERN = re.compile(
    r"grants_permission\s*[:=]\s*(?:true|yes)|skills?\s+(?:may|can)\s+grant\s+permission",
    re.I,
)
UNIVERSAL_SECRET_PATTERNS = (
    ("private key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")),
    (
        "secret assignment",
        re.compile(
            r"\b(?:[a-z0-9]+[_-])*(?:api[_-]?(?:key|token)|access[_-]?key|"
            r"secret(?:[_-]?key)?|client[_-]?secret|password|passwd|token|"
            r"auth[_-]?token|credential(?:s)?|private[_-]?key)\b"
            r"\s*[\"']?\s*[:=]\s*(?:[\"'][^\"'\n]+[\"']|[^\s#,}\]]+)",
            re.I,
        ),
    ),
    (
        "credential URL",
        re.compile(r"\b(?:https?|postgres(?:ql)?|mysql|mongodb(?:\+srv)?)://[^\s/:@]+:[^\s/@]+@", re.I),
    ),
    ("bearer token", re.compile(r"\bBearer\s+[A-Za-z0-9._~+/-]{12,}={0,2}\b", re.I)),
    ("known token format", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16})\b")),
)
PUBLIC_DISCLOSURE_PATTERNS = (
    (
        "private IP address",
        re.compile(
            r"\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|"
            r"172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})\b"
        ),
    ),
    (
        "internal URL or hostname",
        re.compile(r"\bhttps?://[^\s/]*(?:\.internal|\.local|\.corp)(?::\d+)?(?:/|\b)", re.I),
    ),
    (
        "developer-local path",
        re.compile(r"(?:^|[\s'\"])(?:/home/[^/\s]+|/Users/[^/\s]+|[A-Z]:\\Users\\[^\\\s]+)", re.I),
    ),
)
GOVERNANCE_WORKFLOW_PATTERN = re.compile(
    r"(?:governance|auto[-_ ]?remediat|auto[-_ ]?fix|policy[-_ ]?enforc)", re.I
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def add(diagnostics: list[dict[str, str]], status: str, code: str, message: str) -> None:
    item = {"status": status, "code": code, "message": message}
    if item not in diagnostics:
        diagnostics.append(item)


def git(repo: Path, *arguments: str) -> str:
    process = subprocess.run(
        ["git", "-C", str(repo), *arguments],
        check=False,
        capture_output=True,
        text=True,
    )
    if process.returncode != 0:
        detail = process.stderr.strip() or process.stdout.strip() or "unknown git error"
        raise ValueError(f"git {' '.join(arguments)} failed: {detail}")
    return process.stdout.strip()


def normalize_github_remote(remote: str) -> str | None:
    match = GITHUB_REMOTE_PATTERN.fullmatch(remote.strip())
    if match is None:
        return None
    return f"{match.group(1)}/{match.group(2)}".lower()


def load_lock(repo: Path, diagnostics: list[dict[str, str]]) -> dict[str, Any] | None:
    lock_file = repo / LOCK_PATH
    if lock_file.is_symlink() or not lock_file.is_file():
        add(diagnostics, "FAIL", "MISSING_FILE", f"missing or unsafe {LOCK_PATH.as_posix()}")
        add(diagnostics, "FAIL", "LOCK_DRIFT", "governance lock is required")
        return None
    try:
        data = json.loads(lock_file.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        add(diagnostics, "FAIL", "LOCK_DRIFT", f"invalid governance lock: {error}")
        return None
    if not isinstance(data, dict):
        add(diagnostics, "FAIL", "LOCK_DRIFT", "governance lock must be an object")
        return None
    return data


def lock_digest(lock: dict[str, Any]) -> str:
    normalized = copy.deepcopy(lock)
    projection = normalized.get("projection")
    if isinstance(projection, dict):
        files = projection.get("files")
        if isinstance(files, dict):
            files.pop(VALIDATOR_PATH, None)
    payload = json.dumps(normalized, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def validate(repo_argument: Path) -> tuple[dict[str, Any], int]:
    supplied = Path(os.path.abspath(repo_argument))
    diagnostics: list[dict[str, str]] = []
    repository = supplied.name
    expected_profile = "unknown"
    expected_visibility = "unknown"
    public_mode = False
    expected_slug = ""
    try:
        actual_worktree = Path(git(supplied, "rev-parse", "--show-toplevel")).resolve()
        origin_text = git(supplied, "remote", "get-url", "origin")
    except ValueError as error:
        add(diagnostics, "FAIL", "REPOSITORY_IDENTITY", str(error))
        actual_worktree = supplied
        origin = None
    else:
        origin = normalize_github_remote(origin_text)
        if supplied.is_symlink() or supplied != actual_worktree:
            add(
                diagnostics,
                "FAIL",
                "REPOSITORY_IDENTITY",
                f"supplied repository path is not the actual worktree root: {actual_worktree}",
            )
        if origin is None:
            add(diagnostics, "FAIL", "REPOSITORY_IDENTITY", "origin is not a supported GitHub remote")
    expected = EXPECTED_REPOSITORIES.get(origin or "")
    if expected is None:
        add(diagnostics, "FAIL", "REPOSITORY_IDENTITY", f"origin is not a canonical Setvane product: {origin or '<missing>'}")
    else:
        expected_name, expected_profile, expected_visibility, public_mode = expected
        expected_slug = next(slug for slug in EXPECTED_REPOSITORIES if EXPECTED_REPOSITORIES[slug] == expected)
        if actual_worktree.name != expected_name:
            add(
                diagnostics,
                "FAIL",
                "REPOSITORY_IDENTITY",
                f"worktree name {actual_worktree.name} does not match {expected_name}",
            )
        elif not any(item["code"] == "REPOSITORY_IDENTITY" and item["status"] == "FAIL" for item in diagnostics):
            add(diagnostics, "PASS", "REPOSITORY_IDENTITY", f"worktree and origin match {origin}")

    lock = load_lock(actual_worktree, diagnostics)
    profile = expected_profile
    version = SUPPORTED_VERSION
    revision = CANONICAL_REVISION
    projection: dict[str, Any] = {}
    if lock is not None:
        profile = str(lock.get("profile", ""))
        version = str(lock.get("governance_version", ""))
        revision = str(lock.get("canonical_revision", ""))
        checks = (
            (lock.get("schema_version") == "1.1", "LOCK_DRIFT", "lock schema must be 1.1"),
            (lock.get("product") == "setvane", "LOCK_DRIFT", "lock product must be setvane"),
            (lock.get("repository") == repository, "REPOSITORY_IDENTITY", "lock repository does not match worktree"),
            (
                str(lock.get("repository_slug", "")).lower() == expected_slug,
                "REPOSITORY_IDENTITY",
                "lock repository slug does not match origin",
            ),
            (profile == expected_profile, "PROFILE_DRIFT", "lock profile does not match repository profile"),
            (lock.get("visibility") == expected_visibility, "DISCLOSURE_DRIFT", "lock visibility does not match repository visibility"),
            (lock.get("public_mode") is public_mode, "DISCLOSURE_DRIFT", "lock disclosure mode does not match repository visibility"),
            (version == SUPPORTED_VERSION, "VERSION_DRIFT", f"unsupported governance version: {version}"),
            (lock.get("canonical_repository") == CANONICAL_REPOSITORY, "LOCK_DRIFT", "canonical repository does not match V1"),
            (revision == CANONICAL_REVISION, "LOCK_DRIFT", "canonical revision does not match V1"),
            (lock.get("entrypoint") == "AGENTS.md", "LOCK_DRIFT", "entrypoint must be AGENTS.md"),
        )
        for passed, code, message in checks:
            if not passed:
                add(diagnostics, "FAIL", code, message)
        if lock_digest(lock) != EXPECTED_LOCK_DIGEST:
            add(diagnostics, "FAIL", "LOCK_DRIFT", "lock differs from embedded canonical expectations")
        projection_value = lock.get("projection")
        if isinstance(projection_value, dict):
            projection = projection_value
        else:
            add(diagnostics, "FAIL", "LOCK_DRIFT", "lock projection metadata is missing")
        if not any(
            item["status"] == "FAIL"
            and item["code"] in {"LOCK_DRIFT", "PROFILE_DRIFT", "VERSION_DRIFT", "REPOSITORY_IDENTITY"}
            for item in diagnostics
        ):
            add(diagnostics, "PASS", "GOVERNANCE_LOCK", "lock matches embedded canonical expectations")

    files = projection.get("files", {})
    if not isinstance(files, dict):
        add(diagnostics, "FAIL", "LOCK_DRIFT", "projection.files must be an object")
        files = {}
    expected_paths = {Path(str(path)) for path in files}
    for relative_text, expected_hash in sorted(files.items()):
        relative = Path(str(relative_text))
        target = actual_worktree / relative
        if target.is_symlink() or not target.is_file():
            add(diagnostics, "FAIL", "MISSING_FILE", f"missing or unsafe governed file: {relative.as_posix()}")
            continue
        if sha256(target) != expected_hash:
            add(diagnostics, "FAIL", "CONTENT_DRIFT", f"content differs: {relative.as_posix()}")
    if files and not any(
        item["status"] == "FAIL" and item["code"] in {"MISSING_FILE", "CONTENT_DRIFT"}
        for item in diagnostics
    ):
        add(diagnostics, "PASS", "PROJECTION_INTEGRITY", "all governed file hashes match")

    allowed = expected_paths | {LOCK_PATH}
    for root in INVENTORY_ROOTS:
        absolute_root = actual_worktree / root
        if not absolute_root.exists():
            continue
        for path in sorted(item for item in absolute_root.rglob("*") if item.is_file()):
            relative = path.relative_to(actual_worktree)
            if relative not in allowed:
                add(diagnostics, "FAIL", "UNEXPECTED_FILE", f"unexpected governance file: {relative.as_posix()}")
    workflow_root = actual_worktree / ".github/workflows"
    if workflow_root.exists():
        for path in sorted(workflow_root.iterdir()):
            if not path.is_file() or path.suffix.lower() not in {".yml", ".yaml"} or path.name in GOVERNED_WORKFLOWS:
                continue
            try:
                content = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                content = ""
            if GOVERNANCE_WORKFLOW_PATTERN.search(path.name) or GOVERNANCE_WORKFLOW_PATTERN.search(content):
                add(diagnostics, "FAIL", "UNEXPECTED_FILE", f"unexpected governance workflow: .github/workflows/{path.name}")

    text_by_path: dict[str, str] = {}
    for relative in sorted(expected_paths | {LOCK_PATH}):
        target = actual_worktree / relative
        if target.is_file():
            try:
                text_by_path[relative.as_posix()] = target.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                add(diagnostics, "FAIL", "CONTENT_DRIFT", f"governed file is not UTF-8: {relative.as_posix()}")
    combined = "\n".join(content for path, content in text_by_path.items() if path != LOCK_PATH.as_posix())

    markers = projection.get("required_markers", {})
    marker_codes = {
        "identity": "PROFILE_DRIFT",
        "authority": "AUTHORITY_DRIFT",
        "process": "CONTENT_DRIFT",
        "git_safety": "CONTENT_DRIFT",
        "skills": "AUTHORITY_DRIFT",
        "disclosure": "DISCLOSURE_DRIFT",
    }
    if isinstance(markers, dict):
        for group, values in markers.items():
            if not isinstance(values, list):
                add(diagnostics, "FAIL", "LOCK_DRIFT", f"required marker group {group} is invalid")
                continue
            for marker in values:
                if str(marker) not in combined:
                    add(diagnostics, "FAIL", marker_codes.get(str(group), "CONTENT_DRIFT"), f"missing {group} marker: {marker}")
    else:
        add(diagnostics, "FAIL", "LOCK_DRIFT", "required markers must be a mapping")

    references = projection.get("required_references", [])
    if isinstance(references, list):
        for reference in references:
            if str(reference) not in combined:
                add(diagnostics, "FAIL", "REFERENCE_DRIFT", f"missing canonical reference: {reference}")
    else:
        add(diagnostics, "FAIL", "LOCK_DRIFT", "required_references must be a list")

    for pattern in AUTHORITY_PATTERNS.get(profile, ()):
        match = pattern.search(combined)
        if match:
            add(diagnostics, "FAIL", "AUTHORITY_DRIFT", f"authority expansion detected: {match.group(0)}")
    match = SKILL_PERMISSION_PATTERN.search(combined)
    if match:
        add(diagnostics, "FAIL", "AUTHORITY_DRIFT", f"skill permission grant detected: {match.group(0)}")
    if not any(item["status"] == "FAIL" and item["code"] == "AUTHORITY_DRIFT" for item in diagnostics):
        add(diagnostics, "PASS", "AUTHORITY_PROFILE", f"{profile} authority remains fail-closed")

    for relative, content in sorted(text_by_path.items()):
        for label, pattern in UNIVERSAL_SECRET_PATTERNS:
            if pattern.search(content):
                add(diagnostics, "FAIL", "DISCLOSURE_DRIFT", f"{label} detected in governed file: {relative}")
        if public_mode:
            for label, pattern in PUBLIC_DISCLOSURE_PATTERNS:
                if pattern.search(content):
                    add(diagnostics, "FAIL", "DISCLOSURE_DRIFT", f"public {label} detected in governed file: {relative}")
    if not any(item["status"] == "FAIL" and item["code"] == "DISCLOSURE_DRIFT" for item in diagnostics):
        add(diagnostics, "PASS", "DISCLOSURE_PROFILE", f"{expected_visibility} disclosure profile is respected; secrets are forbidden")

    if not any(item["status"] == "FAIL" and item["code"] == "REFERENCE_DRIFT" for item in diagnostics):
        add(diagnostics, "PASS", "CANONICAL_REFERENCES", "required canonical references are present")
    status = "NON_COMPLIANT" if any(item["status"] == "FAIL" for item in diagnostics) else "COMPLIANT"
    exit_code = 1 if status == "NON_COMPLIANT" else 0
    drift = sorted(
        {
            item["code"]
            for item in diagnostics
            if item["status"] == "FAIL"
            and (item["code"].endswith("_DRIFT") or item["code"] in {"MISSING_FILE", "UNEXPECTED_FILE"})
        }
    )
    report = {
        "product": "setvane",
        "repository": repository,
        "profile": profile,
        "governance_version": version,
        "canonical_revision": revision,
        "authority": "ADVISORY_LOCAL_VALIDATOR",
        "diagnostics": diagnostics,
        "drift": drift,
        "status": status,
    }
    return report, exit_code


def print_human(report: dict[str, Any]) -> None:
    print("Setvane Governance Validation (advisory local validator)")
    print()
    print(f"Repository: {report['repository']}")
    print(f"Profile: {report['profile']}")
    print(f"Governance: {report['governance_version']}")
    print(f"Canonical revision: {report['canonical_revision']}")
    print()
    for diagnostic in report["diagnostics"]:
        print(f"{diagnostic['status']} {diagnostic['code']} {diagnostic['message']}")
    print()
    drift = ", ".join(report["drift"]) if report["drift"] else "none"
    print(f"Drift: {drift}")
    print()
    print(f"STATUS: {report['status']}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".", help="repository worktree root to validate")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args()
    report, exit_code = validate(Path(args.repo))
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_human(report)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
