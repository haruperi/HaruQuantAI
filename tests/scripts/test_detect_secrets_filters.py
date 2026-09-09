"""Security regressions for repository-specific detect-secrets filters."""

from __future__ import annotations

import hashlib
import shutil
import subprocess
from pathlib import Path

import pytest

from scripts import detect_secrets_filters


def _git(repo: Path, *args: str) -> str:
    """Run Git in a test repository and return stripped standard output."""
    result = subprocess.run(  # noqa: S603
        ["git", *args],  # noqa: S607
        cwd=repo,
        capture_output=True,
        check=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout.strip()


def _repository(tmp_path: Path) -> str:
    """Create a repository and return its first commit identity."""
    _git(tmp_path, "init", "-b", "main")
    _git(tmp_path, "config", "user.email", "test@example.invalid")
    _git(tmp_path, "config", "user.name", "Test")
    (tmp_path / "README.md").write_text("baseline\n", encoding="utf-8")
    _git(tmp_path, "add", "README.md")
    _git(tmp_path, "commit", "--no-verify", "-m", "baseline")
    return _git(tmp_path, "rev-parse", "HEAD")


@pytest.fixture
def evidence_commit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[Path, str]:
    """Provide a real commit and patch filter ownership to its repository."""
    commit = _repository(tmp_path)
    monkeypatch.setattr(detect_secrets_filters, "REPO", tmp_path)
    path = tmp_path / "docs/dev/evidence/features/FEAT-DT01-FIXTURE/acceptance.json"
    path.parent.mkdir(parents=True)
    return path, commit


def test_real_commit_in_exact_acceptance_field_is_filtered(
    evidence_commit: tuple[Path, str],
) -> None:
    """A real commit is non-secret only in the exact schema-bound location."""
    path, commit = evidence_commit
    line = f'  "baseline_commit": "{commit}",'
    path.write_text("{\n" + line + "\n}\n", encoding="utf-8")

    assert detect_secrets_filters.is_valid_repository_commit_evidence(
        str(path), line, commit
    )


@pytest.mark.parametrize(
    ("relative_path", "field", "suffix"),
    [
        (
            "docs/dev/evidence/features/FEAT-DT01-FIXTURE/acceptance.json",
            "opaque_digest",
            ",",
        ),
        (
            "docs/dev/evidence/features/FEAT-DT01-FIXTURE/other.json",
            "baseline_commit",
            ",",
        ),
        ("docs/dev/evidence/acceptance.json", "baseline_commit", ","),
        (
            "docs/dev/evidence/features/FEAT-DT01-FIXTURE/acceptance.json",
            "baseline_commit",
            ', "opaque_digest": "synthetic"',
        ),
    ],
)
def test_hash_outside_exact_schema_boundary_is_not_filtered(
    evidence_commit: tuple[Path, str],
    relative_path: str,
    field: str,
    suffix: str,
) -> None:
    """Path, field, and whole-line mismatches remain visible to detectors."""
    _, commit = evidence_commit
    path = detect_secrets_filters.REPO / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    line = f'  "{field}": "{commit}"{suffix}'
    path.write_text("{\n" + line + "\n}\n", encoding="utf-8")

    assert not detect_secrets_filters.is_valid_repository_commit_evidence(
        str(path), line, commit
    )


def test_nonexistent_hex_identity_is_not_filtered(
    evidence_commit: tuple[Path, str],
) -> None:
    """A syntactically valid but nonexistent identity fails closed."""
    path, _ = evidence_commit
    nonexistent = "0123456789abcdef" * 2 + "01234567"
    line = f'  "baseline_commit": "{nonexistent}",'
    path.write_text("{\n" + line + "\n}\n", encoding="utf-8")

    assert not detect_secrets_filters.is_valid_repository_commit_evidence(
        str(path), line, nonexistent
    )


def test_external_acceptance_path_is_not_filtered(
    evidence_commit: tuple[Path, str],
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    """A similarly named file outside the repository remains in scan scope."""
    _, commit = evidence_commit
    external = (
        tmp_path_factory.mktemp("external")
        / "docs/dev/evidence/features/FEAT-DT01-FIXTURE/acceptance.json"
    )
    external.parent.mkdir(parents=True)
    line = f'  "baseline_commit": "{commit}",'
    external.write_text("{\n" + line + "\n}\n", encoding="utf-8")

    assert not detect_secrets_filters.is_valid_repository_commit_evidence(
        str(external), line, commit
    )


def test_throughput_snapshot_filters_only_named_real_commit_fields(
    evidence_commit: tuple[Path, str],
) -> None:
    """The bounded DT-01 snapshot can retain exact repository identities."""
    _, commit = evidence_commit
    path = detect_secrets_filters.REPO / (
        "docs/dev/evidence/development-throughput-baseline.json"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    line = f'    "head": "{commit}",'
    path.write_text("{\n" + line + "\n}\n", encoding="utf-8")

    assert detect_secrets_filters.is_valid_repository_commit_evidence(
        str(path), line, commit
    )
    assert not detect_secrets_filters.is_valid_repository_commit_evidence(
        str(path), f'    "opaque_digest": "{commit}",', commit
    )


@pytest.mark.parametrize(
    ("field", "relative_source"),
    [
        (
            "dependency_schedule_sha256",
            "docs/dev/evidence/dependency-schedule.json",
        ),
        ("source_sha256", "docs/dev/milestones/strategy-ready.json"),
    ],
)
def test_strategy_ready_filters_only_current_source_digests(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    relative_source: str,
) -> None:
    """Generated milestone hashes are allowed only when their source matches."""
    monkeypatch.setattr(detect_secrets_filters, "REPO", tmp_path)
    source = tmp_path / relative_source
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("canonical source\n", encoding="utf-8")
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    evidence = tmp_path / "docs/dev/evidence/milestones/strategy-ready.json"
    evidence.parent.mkdir(parents=True, exist_ok=True)
    line = f'  "{field}": "{digest}",'

    assert detect_secrets_filters.is_valid_repository_commit_evidence(
        str(evidence), line, digest
    )
    assert not detect_secrets_filters.is_valid_repository_commit_evidence(
        str(evidence), line, "0" * 64
    )
    assert not detect_secrets_filters.is_valid_repository_commit_evidence(
        str(evidence), f'  "other_sha256": "{digest}",', digest
    )


def test_detect_secrets_still_reports_unapproved_hex(
    tmp_path: Path,
) -> None:
    """The custom filter does not suppress ordinary entropy findings."""
    executable = shutil.which("detect-secrets-hook")
    assert executable is not None
    candidate = tmp_path / "ordinary.json"
    candidate.write_text(
        '{"opaque_digest": "' + ("0123456789abcdef" * 4) + '"}\n',
        encoding="utf-8",
    )
    result = subprocess.run(  # noqa: S603
        [
            executable,
            "--filter",
            "file://scripts/detect_secrets_filters.py::is_valid_repository_commit_evidence",
            str(candidate),
        ],
        cwd=detect_secrets_filters.REPO,
        capture_output=True,
        check=False,
        text=True,
        encoding="utf-8",
    )

    assert result.returncode == 1
    assert "Hex High Entropy String" in result.stdout


def test_detect_secrets_accepts_real_feature_baseline_commit(tmp_path: Path) -> None:
    """The detector loads the file filter and accepts a real feature baseline."""
    commit = _repository(tmp_path)
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    shutil.copyfile(
        detect_secrets_filters.REPO / "scripts/detect_secrets_filters.py",
        scripts / "detect_secrets_filters.py",
    )
    acceptance = (
        tmp_path / "docs/dev/evidence/features/FEAT-DT01-FIXTURE/acceptance.json"
    )
    acceptance.parent.mkdir(parents=True)
    acceptance.write_text(
        '{\n  "baseline_commit": "' + commit + '"\n}\n', encoding="utf-8"
    )
    executable = shutil.which("detect-secrets-hook")
    assert executable is not None

    result = subprocess.run(  # noqa: S603
        [
            executable,
            "--filter",
            "file://scripts/detect_secrets_filters.py::is_valid_repository_commit_evidence",
            acceptance.relative_to(tmp_path).as_posix(),
        ],
        cwd=tmp_path,
        capture_output=True,
        check=False,
        text=True,
        encoding="utf-8",
    )

    assert result.returncode == 0, result.stdout + result.stderr


def test_hook_uses_ephemeral_baseline_copy(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Detector metadata refreshes never modify the tracked baseline input."""
    baseline = tmp_path / "tracked.baseline"
    baseline.write_text("original\n", encoding="utf-8")
    calls: list[Path] = []

    def fake_detect(arguments: list[str]) -> int:
        temporary_baseline = Path(arguments[arguments.index("--baseline") + 1])
        calls.append(temporary_baseline)
        assert temporary_baseline != baseline
        if len(calls) == 1:
            temporary_baseline.write_text("synchronized\n", encoding="utf-8")
            return 3
        assert temporary_baseline.read_text(encoding="utf-8") == "synchronized\n"
        return 0

    monkeypatch.setattr(detect_secrets_filters, "_detect_secrets_main", fake_detect)

    assert detect_secrets_filters.run_secret_scan(["candidate.py"], baseline) == 0
    assert len(calls) == 2
    assert baseline.read_text(encoding="utf-8") == "original\n"
