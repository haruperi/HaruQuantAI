"""Release qualification through boundaries, checks and actual package removal."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.host.packages import scan_packages
from scripts.package_inventory import source_fingerprint
from scripts.removal_check import preflight, qualify, required_cases, run_check


def files_digest(root: Path, names: tuple[str, ...]) -> str:
    """Bind named configuration files and fail if any required file is missing."""
    digest = hashlib.sha256()
    for name in sorted(names):
        digest.update(name.encode())
        digest.update(hashlib.sha256((root / name).read_bytes()).digest())
    return digest.hexdigest()


def evidence_bindings(root: Path) -> dict[str, Any]:
    """Compute source, configuration, dependency and local tool identities."""
    tools = {}
    for name, command in {
        "python": (sys.executable, "--version"),
        "node": ("node", "--version"),
        "typescript": ("node", "app/ui/node_modules/typescript/bin/tsc", "--version"),
    }.items():
        tools[name] = subprocess.check_output(
            command, cwd=root, text=True, timeout=30
        ).strip()
    return {
        "source_sha256": source_fingerprint(root),
        "inventory_sha256": scan_packages(root).fingerprint,
        "config_sha256": files_digest(
            root,
            (
                "pyproject.toml",
                "app/ui/package.json",
                "app/ui/tsconfig.json",
                "app/ui/playwright.config.ts",
                "app/ui/vite.config.ts",
            ),
        ),
        "lockfiles_sha256": files_digest(root, ("uv.lock", "app/ui/package-lock.json")),
        "tools": tools,
    }


def validate_report(root: Path, report: dict[str, Any], evidence: Path) -> list[str]:
    """Reject stale, skipped, partial or absent shipping evidence."""
    issues = preflight(root)
    inventory = scan_packages(root)
    bindings = evidence_bindings(root)
    issues.extend(
        "stale:" + key for key, value in bindings.items() if report.get(key) != value
    )
    shipping = sorted(p.id for p in inventory.packages)
    if report.get("scope") != "release" or report.get("status") != "pass":
        issues.append("Report is not a passing release report")
    if (
        sorted(report.get("shipping_ids", [])) != shipping
        or sorted(report.get("qualified_ids", [])) != shipping
    ):
        issues.append("Shipping qualification is incomplete")
    cases = report.get("cases", [])
    expected = {case.id: case for case in required_cases(inventory)}
    if sorted(case.get("id", "") for case in cases) != sorted(expected):
        issues.append("Required removal matrix is incomplete or duplicated")
    required_checks = {
        "python_survivors",
        "ui_typecheck",
        "ui_tests",
        "ui_build",
        "browser_restart_resources",
    }
    for case in cases:
        spec = expected.get(case.get("id"))
        if (
            spec is None
            or case.get("kind") != spec.kind
            or case.get("target_ids") != list(spec.targets)
        ):
            issues.append("Unexpected removal case identity")
            continue
        closure = set(spec.targets)
        closure.update(
            p.id for p in inventory.packages if p.owner_workspace_id in closure
        )
        removed = sorted(
            {
                name
                for p in inventory.packages
                if p.id in closure
                for name in p.owned_paths.files()
            }
        )
        retained = sorted(p.id for p in inventory.packages if p.id not in closure)
        if (
            case.get("removed_paths") != removed
            or sorted(case.get("retained_ids", [])) != retained
        ):
            issues.append("Wrong removal closure:" + spec.id)
        checks = case.get("checks", [])
        if (
            case.get("status") != "pass"
            or {check.get("id") for check in checks} != required_checks
            or len(checks) != len(required_checks)
        ):
            issues.append("Missing or failed checks:" + spec.id)
        for check in checks:
            name = check.get("evidence_path", "")
            log = evidence / spec.id / name
            if (
                Path(name).name != name
                or not name
                or check.get("status") != "pass"
                or check.get("exit_code") != 0
                or not log.is_file()
            ):
                issues.append("Invalid check evidence:" + spec.id)
                continue
            lines = log.read_text(encoding="utf-8").splitlines()
            if (
                not lines
                or lines[0] != json.dumps({"command": check.get("command")})
                or lines[-1] != json.dumps({"exit_code": 0})
            ):
                issues.append("Check log disagrees with report:" + spec.id)
    if report.get("blockers"):
        issues.append("Unresolved blockers")
    issues.extend(_release_log_issues(evidence))
    return issues


def _release_log_issues(evidence: Path) -> list[str]:
    """Require the checks outside the removal matrix to have passing logs too."""
    issues = []
    for required in ("candidate", "ui_boundaries"):
        log = evidence / (required + ".log")
        if not log.is_file() or not log.read_text(encoding="utf-8").rstrip().endswith(
            json.dumps({"exit_code": 0})
        ):
            issues.append("Missing passing release check:" + required)
    return issues


def main() -> int:
    """Run the shipping checks and generate fresh evidence; never accept an old pass."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    args.report.parent.mkdir(parents=True, exist_ok=True)
    evidence = args.report.parent / (args.report.stem + "-evidence")
    bindings = evidence_bindings(root)
    blockers = preflight(root)
    boundaries = run_check(
        root, evidence, "ui_boundaries", ("node", "scripts/ui_architecture_check.cjs")
    )
    if boundaries["status"] != "pass":
        blockers.append("Frontend ownership/import boundaries failed")
    if not blockers:
        candidate = run_check(
            root, evidence, "candidate", (sys.executable, "scripts/ci_check.py")
        )
        if candidate["status"] != "pass":
            blockers.append("Candidate qualification failed")
    if blockers:
        result = {
            "schema_version": 1,
            "scope": "release",
            "status": "blocked",
            "blockers": blockers,
            "cases": [
                {
                    "id": "baseline",
                    "kind": "baseline",
                    "target_ids": [],
                    "removed_paths": [],
                    "retained_ids": [p.id for p in scan_packages(root).packages],
                    "checks": [boundaries],
                    "status": "blocked",
                }
            ],
            "generated_at": datetime.now(UTC).isoformat(),
            "shipping_ids": [p.id for p in scan_packages(root).packages],
            "qualified_ids": [],
            **bindings,
        }
    else:
        result = {**qualify(root, args.report), **bindings}
        issues = validate_report(root, result, evidence)
        if issues:
            result["status"] = "fail"
            result["blockers"].extend(issues)
    args.report.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("Release qualification:", result["status"])
    return int(result["status"] != "pass")


if __name__ == "__main__":
    raise SystemExit(main())
