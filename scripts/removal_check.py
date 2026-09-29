"""Qualify actual package removal in an isolated installation, never the checkout."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.host.packages import (
    Composition,
    PackageInventory,
    apply_removal,
    plan_removal,
    restore_removal,
    scan_packages,
)
from app.persistence.resources import ResourceStore
from scripts.package_inventory import source_fingerprint, unowned_files

TIMEOUT = 1800


@dataclass(frozen=True)
class Case:
    """Required scenario derived from the shipping inventory, never a fixed list."""

    id: str
    kind: str
    targets: tuple[str, ...]


def required_cases(inventory: PackageInventory) -> tuple[Case, ...]:
    """Enumerate every package, every empty owner, and the empty installation."""
    result = [Case("baseline", "baseline", ())]
    owners = tuple(p.id for p in inventory.packages if p.kind == "workspace")
    for package in inventory.packages:
        result.append(
            Case(
                "remove." + package.id,
                "workspace_cascade"
                if package.kind == "workspace"
                else "plugin_removal",
                (package.id,),
            )
        )
        if package.kind == "workspace":
            result.append(
                Case(
                    "empty." + package.id,
                    "empty_workspace",
                    tuple(
                        p.id
                        for p in inventory.packages
                        if p.owner_workspace_id == package.id
                    ),
                )
            )
    result.append(Case("empty.host", "empty_host", owners))
    result.extend(
        Case(name, kind, ())
        for name, kind in (
            ("invalid.attachment", "invalid_attachment"),
            ("failed.activation", "activation_failure"),
            ("restore.activation", "disable_reinstall"),
            ("producer.absence", "producer_absence"),
            ("unsafe.removal", "unsafe_removal"),
            ("gate.rejection", "negative_gate"),
        )
    )
    return tuple(result)


def run_check(
    root: Path,
    evidence: Path,
    check_id: str,
    command: tuple[str, ...],
    *,
    environment: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Run one bounded real check with a durable log and explicit exit status."""
    evidence.mkdir(parents=True, exist_ok=True)
    path = evidence / (check_id + ".log")
    with path.open("w", encoding="utf-8") as stream:
        stream.write(json.dumps({"command": command}) + "\n")
        stream.flush()
        try:
            completed = subprocess.run(
                command,
                cwd=root,
                stdout=stream,
                stderr=subprocess.STDOUT,
                env=environment,
                timeout=TIMEOUT,
                check=False,
            )
            code = completed.returncode
        except OSError, subprocess.TimeoutExpired:
            code = 124
        stream.write(json.dumps({"exit_code": code}) + "\n")
    return {
        "id": check_id,
        "command": list(command),
        "exit_code": code,
        "status": "pass" if code == 0 else "fail",
        "evidence_path": path.name,
    }


def preflight(root: Path) -> list[str]:
    """Refuse a partial or ambiguous shipping inventory before copying or removing."""
    inventory = scan_packages(root)
    return [
        f"{issue.code}:{issue.path or issue.package_id}" for issue in inventory.issues
    ] + ["unowned:" + name for name in unowned_files(root, inventory)]


def _copy_installation(root: Path, destination: Path) -> None:
    """Copy code and dependencies without real data or generated files."""
    excluded = shutil.ignore_patterns(
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "dist",
        "test-results",
        "playwright-report",
        "*.tsbuildinfo",
        "node_modules",
    )
    for name in ("app", "tests", "scripts", "docs", ".github"):
        if (root / name).exists():
            shutil.copytree(root / name, destination / name, ignore=excluded)
    for name in ("pyproject.toml", "uv.lock", "AGENTS.md", "README.md"):
        shutil.copyfile(root / name, destination / name)
    # No junction: tools may write caches, so dependencies are a private copy too.
    shutil.copytree(root / "app/ui/node_modules", destination / "app/ui/node_modules")


def _browser_check(root: Path, data: Path, evidence: Path) -> dict[str, Any]:
    """Start a real host process and exercise its UI and retained resources."""
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        port = reservation.getsockname()[1]
    url = f"http://127.0.0.1:{port}"
    command = (
        sys.executable,
        "-m",
        "app.main",
        "--port",
        str(port),
        "--data-dir",
        str(data),
    )
    environment = {
        key: value for key, value in os.environ.items() if not key.startswith("HARU_")
    }
    environment.update(
        HARU_TEST_URL=url,
        HARU_REMOVAL_DATA=str(data),
        HARU_INSTALLATION_ROOT=str(root),
    )
    with (evidence / "host.log").open("w", encoding="utf-8") as log:
        process = subprocess.Popen(
            command, cwd=root, stdout=log, stderr=log, env=environment
        )
        try:
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    raise RuntimeError("Isolated host exited during startup")
                try:
                    with urllib.request.urlopen(
                        url + "/api/v1/health", timeout=1
                    ) as response:
                        if response.status == 200:
                            break
                except urllib.error.URLError, TimeoutError:
                    time.sleep(0.1)
            else:
                raise TimeoutError("Isolated host did not become ready")
            return run_check(
                root,
                evidence,
                "browser_restart_resources",
                (
                    "node",
                    "app/ui/node_modules/@playwright/test/cli.js",
                    "test",
                    "--config",
                    "app/ui/playwright.config.ts",
                    "package-removal.spec.ts",
                ),
                environment=environment,
            )
        finally:
            try:
                login = urllib.request.Request(
                    url + "/api/v1/auth/login",
                    data=b"{}",
                    headers={"Content-Type": "application/json"},
                )
                with urllib.request.urlopen(login, timeout=5) as response:
                    token = json.load(response)["data"]["token"]
                shutdown = urllib.request.Request(
                    url + "/api/v1/shutdown",
                    data=b"{}",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": "Bearer " + token,
                    },
                )
                with urllib.request.urlopen(shutdown, timeout=5):
                    pass
                process.wait(timeout=10)
            except OSError, ValueError, KeyError, subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=10)
                raise RuntimeError("Isolated host did not shut down cleanly") from None


def _scenario_invalid_attachment() -> None:
    """Verify scanner isolates invalid attachment slot definitions."""
    from tests.host.test_packages import make_package

    with tempfile.TemporaryDirectory() as td:
        scratch = Path(td)
        make_package(scratch, "workspace")
        make_package(scratch, "child", "test.workspace")
        manifest = scratch / "app/ui/app/plugins/child/package.json"
        doc = json.loads(manifest.read_text(encoding="utf-8"))
        doc["attachment"]["slot_id"] = "nonexistent_slot_404"
        manifest.write_text(json.dumps(doc), encoding="utf-8")
        inv = scan_packages(scratch)
        has_issue = any(
            issue.package_id == doc["id"]
            or issue.code in ("invalid_package", "unowned_file")
            for issue in inv.issues
        )
        if not has_issue:
            raise AssertionError("Invalid attachment was not rejected by scanner")


def _scenario_activation_failure() -> None:
    """Verify failing package activation is isolated in composition."""
    import asyncio

    from app.host.jobs import JobManager
    from tests.host.test_composition import package

    with tempfile.TemporaryDirectory() as td:
        scratch = Path(td)
        package(scratch, "owner")
        package(scratch, "good", "test.owner")
        package(scratch, "bad", "test.owner", failure=True)
        comp = Composition(scratch, ResourceStore(scratch / "res"), JobManager(1, 1024))
        inv = scan_packages(scratch)
        asyncio.run(comp.start(inv))
        if "test.good" not in comp.active or "test.bad" in comp.active:
            raise AssertionError(
                "Failing package was not isolated from healthy package"
            )


def _scenario_disable_reinstall() -> None:
    """Verify removal and journaled restoration restores original fingerprint."""
    from tests.host.test_packages import make_package

    with tempfile.TemporaryDirectory() as td:
        scratch = Path(td)
        make_package(scratch, "workspace")
        make_package(scratch, "child", "test.workspace")
        inv_before = scan_packages(scratch)
        target = "test.child"
        plan = plan_removal(scratch, inv_before, target)
        journal = apply_removal(scratch, plan)
        if scan_packages(scratch).fingerprint == inv_before.fingerprint:
            raise AssertionError("Removal did not alter fingerprint")
        restore_removal(scratch, journal)
        if scan_packages(scratch).fingerprint != inv_before.fingerprint:
            raise AssertionError("Reinstallation did not restore identical fingerprint")


def _scenario_producer_absence() -> None:
    """Verify consumer can read independent resource published by removed producer."""
    with tempfile.TemporaryDirectory() as td:
        store = ResourceStore(Path(td) / "resources")
        ref = store.publish(
            "temp.producer",
            "1.0.0",
            b"consumer data payload",
            schema_id="test.schema",
            schema_version="1.0.0",
            schema_json='{"type": "string"}',
            media_type="text/plain",
            readers=("independent.consumer",),
        )
        content, schema_document = store.read("independent.consumer", ref)
        if (
            content != b"consumer data payload"
            or schema_document != '{"type": "string"}'
        ):
            raise AssertionError("Consumer read failed in producer absence")


def _scenario_unsafe_removal(root: Path) -> None:
    """Verify unsafe removal targets fail closed."""
    inv = scan_packages(root)
    for bad_target in ("../traversal", "nonexistent.package", "host"):
        try:
            plan_removal(root, inv, bad_target)
            raise AssertionError(f"Expected plan_removal to fail on: {bad_target}")
        except ValueError, KeyError:
            pass


def _scenario_negative_gate(root: Path) -> None:
    """Verify release gate rejects corrupt or invalid evidence."""
    from scripts.release_check import validate_report

    with tempfile.TemporaryDirectory() as td:
        fake_evidence = Path(td) / "ev"
        fake_evidence.mkdir()
        bad_report: dict[str, Any] = {
            "scope": "release",
            "status": "fail",
            "shipping_ids": [],
            "qualified_ids": [],
            "source_sha256": "bad",
            "blockers": ["some_blocker"],
            "cases": [],
        }
        issues = validate_report(root, bad_report, fake_evidence)
        if not issues:
            raise AssertionError("Gate did not reject bad report")


def _run_supplemental_scenario(root: Path, _data: Path, kind: str) -> None:
    """Execute dedicated verification for supplemental qualification cases."""
    handlers: dict[str, Callable[[], None]] = {
        "invalid_attachment": _scenario_invalid_attachment,
        "activation_failure": _scenario_activation_failure,
        "disable_reinstall": _scenario_disable_reinstall,
        "producer_absence": _scenario_producer_absence,
        "unsafe_removal": lambda: _scenario_unsafe_removal(root),
        "negative_gate": lambda: _scenario_negative_gate(root),
    }
    action = handlers.get(kind)
    if action is not None:
        action()


def execute_case(root: Path, data: Path, case: Case, evidence: Path) -> dict[str, Any]:
    """Remove exact packages, run surviving code/tests, then restore and rescan."""
    if case.kind in (
        "invalid_attachment",
        "activation_failure",
        "disable_reinstall",
        "producer_absence",
        "unsafe_removal",
        "negative_gate",
    ):
        _run_supplemental_scenario(root, data, case.kind)
    before = scan_packages(root)
    journals: list[Path] = []
    removed: list[str] = []
    checks: list[dict[str, Any]] = []
    try:
        for target in case.targets:
            inventory = scan_packages(root)
            plan = plan_removal(root, inventory, target)
            journals.append(apply_removal(root, plan))
            removed.extend(plan.files)
        retained = scan_packages(root)
        if retained.issues or any((root / name).exists() for name in removed):
            raise ValueError("Removal did not produce a complete survivor inventory")
        commands = (
            (
                "python_survivors",
                (sys.executable, "-m", "pytest", "tests", "--no-cov", "-q"),
            ),
            (
                "ui_typecheck",
                (
                    "node",
                    "app/ui/node_modules/typescript/bin/tsc",
                    "-b",
                    "app/ui/tsconfig.json",
                ),
            ),
            (
                "ui_tests",
                (
                    "node",
                    "app/ui/node_modules/vitest/vitest.mjs",
                    "run",
                    "--root",
                    "app/ui",
                ),
            ),
            (
                "ui_build",
                (
                    "node",
                    "app/ui/node_modules/vite/bin/vite.js",
                    "build",
                    "app/ui",
                    "--config",
                    "app/ui/vite.config.ts",
                ),
            ),
        )
        for name, command in commands:
            checks.append(run_check(root, evidence, name, command))
        checks.append(_browser_check(root, data, evidence))
        result = {
            "id": case.id,
            "kind": case.kind,
            "target_ids": list(case.targets),
            "removed_paths": sorted(set(removed)),
            "retained_ids": [p.id for p in retained.packages],
            "checks": checks,
            "status": "pass" if all(c["status"] == "pass" for c in checks) else "fail",
        }
    finally:
        for journal in reversed(journals):
            restore_removal(root, journal)
        if scan_packages(root).fingerprint != before.fingerprint:
            raise ValueError("Reinstall did not restore the exact original inventory")
    return result


def qualify(root: Path, report: Path) -> dict[str, Any]:
    """Run an exhaustive disposable matrix; partial evidence never passes."""
    inventory = scan_packages(root)
    result: dict[str, Any] = {
        "schema_version": 1,
        "scope": "release",
        "status": "fail",
        "source_sha256": source_fingerprint(root),
        "inventory_sha256": inventory.fingerprint,
        "generated_at": datetime.now(UTC).isoformat(),
        "shipping_ids": [p.id for p in inventory.packages],
        "qualified_ids": [],
        "cases": [],
        "blockers": preflight(root),
    }
    if result["blockers"]:
        return result
    evidence = report.parent / (report.stem + "-evidence")
    evidence.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="haru-removal-") as temporary:
        sandbox = Path(temporary).resolve()
        if not sandbox.is_relative_to(Path(tempfile.gettempdir()).resolve()):
            raise ValueError("Invalid temporary boundary")
        installation = sandbox / "installation"
        installation.mkdir()
        _copy_installation(root, installation)
        data = sandbox / "retained-data"
        reference = ResourceStore(data / "resources").publish(
            "removed.producer",
            "1.0.0",
            b"retained independent resource",
            schema_id="qualification.bytes",
            schema_version="1.0.0",
            schema_json='{"type":"string"}',
            media_type="text/plain",
            readers=("*",),
        )
        record = data / "resources" / f"{reference.id}.1.json"
        original = hashlib.sha256(record.read_bytes()).hexdigest()
        for case in required_cases(inventory):
            print("Removal qualification:", case.id, flush=True)
            result["cases"].append(
                execute_case(installation, data, case, evidence / case.id)
            )
            if hashlib.sha256(record.read_bytes()).hexdigest() != original:
                result["blockers"].append("Retained resource changed")
            report.write_text(json.dumps(result, indent=2), encoding="utf-8")
    if not result["blockers"] and all(c["status"] == "pass" for c in result["cases"]):
        result["status"] = "pass"
        result["qualified_ids"] = result["shipping_ids"]
    return result


def main() -> int:
    """Write evidence even when the candidate is blocked before destructive tests."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    args.report.parent.mkdir(parents=True, exist_ok=True)
    result = qualify(Path(__file__).resolve().parents[1], args.report)
    args.report.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return int(result["status"] != "pass")


if __name__ == "__main__":
    raise SystemExit(main())
