"""Narrow detect-secrets filters for deterministic repository evidence."""

from __future__ import annotations

import argparse
import contextlib
import hashlib
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
_BASELINE_COMMIT_LINE_RE = re.compile(
    r'^\s*"baseline_commit"\s*:\s*"(?P<commit>[a-f0-9]{40})"\s*,?\s*$'
)
_THROUGHPUT_COMMIT_LINE_RE = re.compile(
    r'^\s*"(?:head|upstream_head)"\s*:\s*"(?P<commit>[a-f0-9]{40})"\s*,?\s*$'
)
_STRATEGY_READY_PATH = "docs/dev/evidence/milestones/strategy-ready.json"
_STRATEGY_READY_DIGEST_LINE_RE = re.compile(
    r'^\s*"(?P<field>dependency_schedule_sha256|source_sha256)"\s*:\s*'
    r'"(?P<digest>[a-f0-9]{64})"\s*,?\s*$'
)
_STRATEGY_READY_DIGEST_SOURCES = {
    "dependency_schedule_sha256": "docs/dev/evidence/dependency-schedule.json",
    "source_sha256": "docs/dev/milestones/strategy-ready.json",
}


def _repository_relative_path(filename: str) -> str | None:
    """Return a normalized repository-relative path when it is inside the repo.

    Args:
        filename: Path supplied by detect-secrets.

    Returns:
        POSIX repository-relative path, or ``None`` for an external path.
    """
    candidate = Path(filename)
    if not candidate.is_absolute():
        candidate = REPO / candidate
    try:
        return candidate.resolve().relative_to(REPO.resolve()).as_posix()
    except OSError, ValueError:
        return None


def _is_repository_commit(object_id: str) -> bool:
    """Return whether an object ID resolves to a commit in this repository.

    Args:
        object_id: Full lowercase hexadecimal Git object identity.

    Returns:
        ``True`` only when Git resolves the identity as a commit object.
    """
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


def _is_current_strategy_ready_digest(field: str, digest: str) -> bool:
    """Return whether a milestone digest matches its exact generated source."""
    relative_source = _STRATEGY_READY_DIGEST_SOURCES.get(field)
    if relative_source is None:
        return False
    try:
        source_bytes = (REPO / relative_source).read_bytes()
    except OSError:
        return False
    return hashlib.sha256(source_bytes).hexdigest() == digest


def is_valid_repository_commit_evidence(
    filename: str,
    line: str,
    secret: str,
) -> bool:
    """Filter one schema-bound repository identity that is a real Git commit.

    Args:
        filename: File currently scanned by detect-secrets.
        line: Complete source line containing the finding.
        secret: Candidate secret value reported by a detector.

    Returns:
        ``True`` only for an approved commit field in its exact evidence document
        when the value resolves to a repository commit.
    """
    relative_path = _repository_relative_path(filename)
    if relative_path is None:
        return False
    if _ACCEPTANCE_PATH_RE.fullmatch(relative_path):
        match = _BASELINE_COMMIT_LINE_RE.fullmatch(line)
    elif relative_path == "docs/dev/evidence/development-throughput-baseline.json":
        match = _THROUGHPUT_COMMIT_LINE_RE.fullmatch(line)
    elif relative_path == _STRATEGY_READY_PATH:
        digest_match = _STRATEGY_READY_DIGEST_LINE_RE.fullmatch(line)
        if digest_match is None or digest_match.group("digest") != secret:
            return False
        return _is_current_strategy_ready_digest(
            digest_match.group("field"), digest_match.group("digest")
        )
    else:
        return False
    if match is None or match.group("commit") != secret:
        return False
    return _is_repository_commit(secret)


def run_secret_scan(filenames: list[str], baseline_path: Path) -> int:
    """Scan files against an ephemeral synchronized copy of the secret baseline.

    Args:
        filenames: Repository files supplied by pre-commit.
        baseline_path: Tracked detect-secrets baseline used as read-only input.

    Returns:
        Detect-secrets-compatible process exit status.

    Raises:
        OSError: If the baseline cannot be copied into temporary storage.
    """
    if not filenames:
        return 0
    filter_spec = (
        "file://scripts/detect_secrets_filters.py::is_valid_repository_commit_evidence"
    )
    with tempfile.TemporaryDirectory(prefix="haruquantai-secret-scan-") as temp_dir:
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
    """Run the non-mutating repository secret-scanning hook.

    Args:
        argv: Optional command-line arguments for tests.

    Returns:
        Zero on a clean scan and the detector status otherwise.
    """
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
