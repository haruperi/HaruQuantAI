"""Finalize one generated L5 certificate with reproducible audit evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import subprocess
from collections.abc import Callable, Sequence
from pathlib import Path

from tests.simulator.integration.l5_certificate_collection import (
    validate_l5_certificate_bundle,
)

_HASHED_MEMBERS = (
    "commands.txt",
    "comparison.json",
    "environment.json",
    "left-evidence.json",
    "manifest.json",
    "normalized-left.json",
    "normalized-right.json",
    "right-evidence.json",
)
_SENSITIVE_ARGUMENTS = (
    "account_id",
    "api_key",
    "auth_token",
    "credential",
    "login",
    "password",
    "secret",
    "terminal_path",
)
type AuditRunner = Callable[[Sequence[str], Path], int]


def _digest(path: Path) -> str:
    """Return one file's lowercase SHA-256 digest."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_required_audit_commands(bundle: Path) -> tuple[tuple[str, ...], ...]:
    """Build the exact repository-relative offline publication commands.

    Args:
        bundle: Repository-relative certificate bundle path.

    Returns:
        Ordered argument tuples for every mandatory offline gate.

    Raises:
        ValueError: If the bundle path is absolute or escapes the repository.
    """
    if bundle.is_absolute() or ".." in bundle.parts:
        raise ValueError("certificate audit bundle must be repository-relative")
    bundle_text = bundle.as_posix()
    return (
        (
            "uv",
            "run",
            "python",
            "tests/simulator/integration/l5_certificate_finalize.py",
            "--validate-only",
            "--bundle",
            bundle_text,
        ),
        (
            "uv",
            "run",
            "python",
            "tests/simulator/integration/l5_certificate_finalize.py",
            "--scan-only",
            "--bundle",
            bundle_text,
        ),
        (
            "uv",
            "run",
            "pytest",
            "--no-cov",
            "tests/simulator/integration/test_l5_certificate_collection.py",
            "tests/simulator/integration/test_l5_certificate_bundle.py",
            "tests/simulator/integration/test_parity_relationships.py",
            "-q",
        ),
        ("uv", "run", "pytest", "--no-cov", "tests/simulator", "-q"),
        ("uv", "run", "python", "tests/simulator/usage/features/18_parity.py"),
        ("uv", "run", "ruff", "check", "."),
        ("uv", "run", "ruff", "format", "--check", "."),
        ("uv", "run", "mypy", "."),
    )


def validate_finalized_command_ledger(bundle: Path, workspace_root: Path) -> None:
    """Validate exact successful commands for one finalized certificate.

    Args:
        bundle: Resolved certificate bundle directory.
        workspace_root: Repository root containing the artifact tree.

    Raises:
        ValueError: If the ledger is incomplete, unsafe, or non-reproducible.
    """
    root = workspace_root.resolve()
    resolved = bundle.resolve()
    artifact_root = (root / "artifacts" / "sim_live_parity").resolve()
    if not resolved.is_relative_to(artifact_root):
        raise ValueError("certificate bundle escapes the artifact root")
    relative = resolved.relative_to(root)
    lines = (resolved / "commands.txt").read_text(encoding="utf-8").splitlines()
    if len(lines) != 1 + len(build_required_audit_commands(relative)):
        raise ValueError("certificate command ledger is incomplete")
    parsed: list[tuple[str, ...]] = []
    for line in lines:
        prefix, separator, command = line.partition("\t")
        if separator != "\t" or prefix != "exit_code=0" or not command:
            raise ValueError("certificate command ledger contains a failed command")
        if any(fragment in command.casefold() for fragment in _SENSITIVE_ARGUMENTS):
            raise ValueError("certificate command ledger contains sensitive material")
        parsed.append(tuple(shlex.split(command)))
    collector = parsed[0]
    if (
        "tests/simulator/integration/l5_certificate_collection.py" not in collector
        or "--execute-demo" not in collector
        or "--output" not in collector
        or collector[collector.index("--output") + 1] != relative.as_posix()
    ):
        raise ValueError("certificate collector command is not reproducible")
    if tuple(parsed[1:]) != build_required_audit_commands(relative):
        raise ValueError("certificate audit command ledger differs")


def _run_command(arguments: Sequence[str], workspace_root: Path) -> int:
    """Run one exact offline audit command without a shell.

    Args:
        arguments: Tokenized repository-relative command.
        workspace_root: Repository root used as the working directory.

    Returns:
        Process exit code.
    """
    result = subprocess.run(  # noqa: S603 - arguments are an exact internal allowlist.
        arguments,
        cwd=workspace_root,
        check=False,
    )
    return result.returncode


def scan_certificate_for_sensitive_values(bundle: Path, workspace_root: Path) -> None:
    """Fail when the external scanner reports any candidate bundle finding.

    Args:
        bundle: Resolved certificate bundle directory.
        workspace_root: Repository root used as the working directory.

    Raises:
        RuntimeError: If scanning fails, output is malformed, or findings exist.
    """
    arguments = ("uv", "run", "detect-secrets", "scan", str(bundle))
    result = subprocess.run(  # noqa: S603 - executable and arguments are fixed here.
        arguments,
        cwd=workspace_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError("certificate sensitive-value scan failed")
    try:
        findings = json.loads(result.stdout).get("results", {})
    except (AttributeError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            "certificate sensitive-value scan output is malformed"
        ) from exc
    if any(findings.values()):
        raise RuntimeError("certificate sensitive-value scan found prohibited material")


def finalize_certificate_command_evidence(
    bundle: Path,
    *,
    workspace_root: Path,
    runner: AuditRunner = _run_command,
) -> None:
    """Run mandatory audits and atomically finalize their command ledger.

    Args:
        bundle: Existing unfinalized certificate bundle.
        workspace_root: Repository root containing the artifact tree.
        runner: Injectable shell-free audit command runner.

    Raises:
        RuntimeError: If an audit command fails.
        ValueError: If the candidate or command ledger is unsafe.
    """
    root = workspace_root.resolve()
    resolved = bundle.resolve()
    artifact_root = (root / "artifacts" / "sim_live_parity").resolve()
    if not resolved.is_relative_to(artifact_root):
        raise ValueError("certificate bundle escapes the artifact root")
    validate_l5_certificate_bundle(resolved)
    commands_path = resolved / "commands.txt"
    checksums_path = resolved / "checksums.sha256"
    original_commands = commands_path.read_bytes()
    original_checksums = checksums_path.read_bytes()
    collector_lines = original_commands.decode("utf-8").splitlines()
    if len(collector_lines) != 1 or collector_lines[0].startswith("exit_code="):
        raise ValueError(
            "certificate command evidence is already finalized or malformed"
        )
    relative = resolved.relative_to(root)
    audits = build_required_audit_commands(relative)
    completed: list[tuple[str, ...]] = []
    for arguments in audits:
        exit_code = runner(arguments, root)
        if exit_code != 0:
            message = f"certificate audit command failed with exit code {exit_code}"
            raise RuntimeError(message)
        completed.append(tuple(arguments))
    ledger = [f"exit_code=0\t{collector_lines[0]}"]
    ledger.extend(f"exit_code=0\t{shlex.join(arguments)}" for arguments in completed)
    try:
        commands_path.write_text("\n".join(ledger) + "\n", encoding="utf-8")
        checksum_lines = [
            f"{_digest(resolved / name)}  {name}" for name in _HASHED_MEMBERS
        ]
        checksums_path.write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")
        validate_l5_certificate_bundle(resolved)
        validate_finalized_command_ledger(resolved, root)
    except Exception:
        commands_path.write_bytes(original_commands)
        checksums_path.write_bytes(original_checksums)
        raise


def _arguments() -> argparse.Namespace:
    """Parse finalizer arguments.

    Returns:
        Validated raw command-line namespace.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", required=True, type=Path)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--scan-only", action="store_true")
    return parser.parse_args()


def main() -> None:
    """Validate or finalize one repository-local certificate bundle."""
    args = _arguments()
    root = Path.cwd().resolve()
    bundle = (
        (root / args.bundle).resolve()
        if not args.bundle.is_absolute()
        else args.bundle.resolve()
    )
    if args.validate_only:
        validate_l5_certificate_bundle(bundle)
        print("Certificate candidate validation passed")
        return
    if args.scan_only:
        scan_certificate_for_sensitive_values(bundle, root)
        print("Certificate candidate sensitive-value scan passed")
        return
    finalize_certificate_command_evidence(bundle, workspace_root=root)
    print("Certificate command evidence finalized")


if __name__ == "__main__":
    main()
