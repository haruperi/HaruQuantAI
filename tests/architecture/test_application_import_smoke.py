"""Subprocess application import smoke tests verifying clean-process startup."""

from __future__ import annotations

from pathlib import Path

from tests.removability.harness import run_in_fresh_process

_REPO_ROOT = Path(__file__).resolve().parents[2]


def test_application_imports_in_fresh_process() -> None:
    """Verify that importing the application succeeds in a fresh isolated Python interpreter."""
    smoke_script = (
        "import app\n"
        "from app.main import async_main\n"
        "assert callable(async_main)\n"
        "print('IMPORT_OK')\n"
    )

    result = run_in_fresh_process(
        repository_root=_REPO_ROOT,
        script=smoke_script,
        timeout_seconds=30.0,
    )

    assert result.returncode == 0, (
        f"Fresh process import failed with exit code {result.returncode}:\n"
        f"  STDOUT: {result.stdout}\n"
        f"  STDERR: {result.stderr}"
    )
    assert "IMPORT_OK" in result.stdout, (
        f"Expected 'IMPORT_OK' in stdout, got: {result.stdout!r}"
    )
    assert result.stderr == "", f"Unexpected stderr: {result.stderr!r}"


def test_fresh_process_reports_failure() -> None:
    """Verify that the fresh process harness correctly propagates non-zero exit codes."""
    failure_script = "raise SystemExit(7)\n"

    result = run_in_fresh_process(
        repository_root=_REPO_ROOT,
        script=failure_script,
        timeout_seconds=30.0,
    )

    assert result.returncode == 7, f"Expected returncode 7, got {result.returncode}"
