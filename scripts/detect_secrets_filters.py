"""Narrow detect-secrets filters for deterministic repository evidence."""

from __future__ import annotations

import argparse
import contextlib
import io
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from detect_secrets.pre_commit_hook import main as _detect_secrets_main

REPO = Path(__file__).resolve().parent.parent
_BASELINE_UPDATED_EXIT = 3
_ACCEPTANCE_PATH_RE = re.compile(
    r"^docs/dev/evidence/features/FEAT-[A-Z0-9_-]+/acceptance\.json$"
)
_REIMPLEMENTATION_PATH = "docs/dev/evidence/reimplementation.json"
_BASELINE_COMMIT_LINE_RE = re.compile(
    r'^\s*"(?:baseline_commit|tested_revision)"\s*:\s*"(?P<commit>[a-f0-9]{40})"\s*,?\s*$'
)
_REIMPLEMENTATION_COMMIT_LINE_RE = re.compile(
    r'^\s*"repository_commit"\s*:\s*"(?P<commit>[a-f0-9]{40})"\s*,?\s*$'
)
_FINGERPRINT_HASH_LINE_RE = re.compile(
    r'^\s*"(?:owner_module_sha256|public_contract_sha256|domain_readme_sha256)"\s*:\s*"(?P<hash>[a-f0-9]{64})"\s*,?\s*$'
)
_REIMPLEMENTATION_FINGERPRINT_LINE_RE = re.compile(
    r'^\s*"value"\s*:\s*"(?P<hash>[a-f0-9]{64})"\s*,?\s*$'
)
# Evidence artifact locators under the logical roots. Values are plain
# repository/donor paths (letters, digits, underscore, dot, slash, dash);
# long mixed-case paths otherwise trip the base64 entropy heuristic.
_REIMPLEMENTATION_ARTIFACT_PATH_LINE_RE = re.compile(
    r'^\s*(?:"artifact_locator"\s*:\s*)?'
    r'"(?P<path>(?:SQX_REFERENCE_ROOT|HARUQUANTAI_ROOT)/[A-Za-z0-9_./-]+)"'
    r"\s*,?\s*$"
)


def _repository_relative_path(filename: str) -> str | None:
    """Return a normalized repository-relative path when inside the repo."""
    candidate = Path(filename)
    if not candidate.is_absolute():
        candidate = REPO / candidate
    try:
        return candidate.resolve().relative_to(REPO.resolve()).as_posix()
    except OSError, ValueError:
        return None


def _is_repository_commit(object_id: str) -> bool:
    """Return whether an object ID resolves to a commit in this repository."""
    try:
        result = subprocess.run(
            ["git", "cat-file", "-e", f"{object_id}^{{commit}}"],
            cwd=REPO,
            capture_output=True,
            check=False,
        )
    except OSError:
        return False
    return result.returncode == 0


def is_valid_repository_commit_evidence(
    filename: str,
    line: str,
    secret: str,
) -> bool:
    """Filter one schema-bound repository identity that is a real Git commit."""
    relative_path = _repository_relative_path(filename)
    if relative_path is None:
        return False
    if _ACCEPTANCE_PATH_RE.fullmatch(relative_path):
        match = _BASELINE_COMMIT_LINE_RE.fullmatch(line)
    elif relative_path == _REIMPLEMENTATION_PATH:
        match = _REIMPLEMENTATION_COMMIT_LINE_RE.fullmatch(line)
    else:
        return False
    if match is None or match.group("commit") != secret:
        return False
    return _is_repository_commit(secret)


def is_valid_repository_fingerprint_evidence(
    filename: str,
    line: str,
    secret: str,
) -> bool:
    """Filter schema-bound file fingerprint SHA256 hashes in acceptance manifests."""
    relative_path = _repository_relative_path(filename)
    if relative_path is None:
        return False
    if _ACCEPTANCE_PATH_RE.fullmatch(relative_path):
        match = _FINGERPRINT_HASH_LINE_RE.fullmatch(line)
    elif relative_path == _REIMPLEMENTATION_PATH:
        match = _REIMPLEMENTATION_FINGERPRINT_LINE_RE.fullmatch(line)
    else:
        return False
    if match is None or match.group("hash") != secret:
        return False
    return True


def is_valid_repository_artifact_path_evidence(
    filename: str,
    line: str,
    secret: str,
) -> bool:
    """Filter schema-bound logical-root artifact locator paths in the ledger.

    Long mixed-case donor/repository paths under SQX_REFERENCE_ROOT or
    HARUQUANTAI_ROOT can trip the base64 entropy heuristic although they are
    evidence locators, not secrets.
    """
    relative_path = _repository_relative_path(filename)
    if relative_path != _REIMPLEMENTATION_PATH:
        return False
    match = _REIMPLEMENTATION_ARTIFACT_PATH_LINE_RE.fullmatch(line)
    if match is None:
        return False
    return match.group("path").rstrip("/") == secret.rstrip("/")


def is_valid_repository_evidence(
    filename: str,
    line: str,
    secret: str,
) -> bool:
    """Filter supported schema-bound repository evidence identities."""
    return (
        is_valid_repository_commit_evidence(filename, line, secret)
        or is_valid_repository_fingerprint_evidence(filename, line, secret)
        or is_valid_repository_artifact_path_evidence(filename, line, secret)
    )


def run_secret_scan(filenames: list[str], baseline_path: Path) -> int:
    """Run detect-secrets without mutating the tracked baseline file."""
    if not filenames:
        return 0
    filter_spec = (
        "file://scripts/detect_secrets_filters.py::is_valid_repository_evidence"
    )
    with tempfile.TemporaryDirectory(prefix="template-secret-scan-") as temp_dir:
        temporary_baseline = Path(temp_dir) / ".secrets.baseline"
        shutil.copyfile(baseline_path, temporary_baseline)
        arguments = [
            "--baseline",
            str(temporary_baseline),
            "--filter",
            filter_spec,
            *filenames,
        ]
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured), contextlib.redirect_stderr(captured):
            result = _detect_secrets_main(arguments)
        if result == _BASELINE_UPDATED_EXIT:
            captured = io.StringIO()
            with (
                contextlib.redirect_stdout(captured),
                contextlib.redirect_stderr(captured),
            ):
                result = _detect_secrets_main(arguments)
        if result != 0:
            print(captured.getvalue(), end="")
        return result


def main(argv: list[str] | None = None) -> int:
    """Run the non-mutating repository secret-scanning hook."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--baseline",
        type=Path,
        default=REPO / ".github/.secrets.baseline",
        help="tracked baseline to read without modifying",
    )
    parser.add_argument("filenames", nargs="*")
    args = parser.parse_args(argv)
    return run_secret_scan(args.filenames, args.baseline)


if __name__ == "__main__":
    sys.exit(main())
