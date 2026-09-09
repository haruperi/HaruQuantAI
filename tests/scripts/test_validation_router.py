"""Tests for conservative validation impact routing."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from scripts import validation_router


def _git(repo: Path, *arguments: str) -> str:
    """Run Git in a fixture repository and return standard output."""
    result = subprocess.run(  # noqa: S603
        ["git", *arguments],  # noqa: S607
        cwd=repo,
        capture_output=True,
        check=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout.strip()


def _write(repo: Path, relative: str, content: str = "fixture\n") -> Path:
    """Write one fixture file below the repository root."""
    path = repo / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


@pytest.fixture
def repository(tmp_path: Path) -> tuple[Path, str]:
    """Provide a clean Git repository with one baseline commit."""
    _git(tmp_path, "init", "-b", "main")
    _git(tmp_path, "config", "user.email", "test@example.invalid")
    _git(tmp_path, "config", "user.name", "Test")
    _write(tmp_path, "README.md")
    _git(tmp_path, "add", "README.md")
    _git(tmp_path, "commit", "--no-verify", "-m", "baseline")
    return tmp_path, _git(tmp_path, "rev-parse", "HEAD")


def test_ui_only_affected_route_selects_no_python(
    repository: tuple[Path, str],
) -> None:
    """A local UI widget edit selects bounded UI checks only."""
    repo, _ = repository
    _write(repo, "app/ui/src/widgets/orders/OrderTicket.tsx")
    _write(repo, "app/ui/src/widgets/orders/OrderTicket.test.tsx")

    decision = validation_router.route_validation(repo, profile="affected")

    assert decision.families == ("ui-affected",)
    assert decision.ui_test_paths == ("src/widgets/orders",)
    assert "python" not in decision.families


def test_python_feature_maps_owner_and_domain_integration_tests(
    repository: tuple[Path, str],
) -> None:
    """A Python feature edit includes its owner and consumer integration tests."""
    repo, _ = repository
    _write(repo, "app/services/workspace/manage_artifacts/service.py")
    _write(repo, "tests/services/workspace/manage_artifacts/test_service.py")
    _write(repo, "tests/services/workspace/integration/test_manage_artifacts.py")

    decision = validation_router.route_validation(repo, profile="affected")

    assert decision.families == ("python-affected",)
    assert decision.python_test_paths == (
        "tests/services/workspace/integration",
        "tests/services/workspace/manage_artifacts",
    )


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("app/contracts/workspace/artifacts.py", ("python", "ui")),
        ("app/kernel/lifecycle.py", ("python", "ui")),
        ("app/composition/engine.py", ("python", "ui")),
        ("docs/templates/prompt/planner.md", ("workflow",)),
        ("docs/dev/notes.md", ("documentation",)),
        ("pyproject.toml", validation_router.FULL_FAMILIES),
        ("tests/conftest.py", validation_router.FULL_FAMILIES),
        ("uv.lock", validation_router.FULL_FAMILIES),
        ("unexpected.bin", validation_router.FULL_FAMILIES),
    ],
)
def test_conservative_path_classes(
    repository: tuple[Path, str], path: str, expected: tuple[str, ...]
) -> None:
    """Known shared, workflow, documentation, and uncertain paths route safely."""
    repo, _ = repository
    _write(repo, path)

    decision = validation_router.route_validation(repo, profile="affected")

    assert decision.families == expected


def test_integration_routes_python_feature_to_comprehensive_python(
    repository: tuple[Path, str],
) -> None:
    """Integration routing expands a committed feature edit to Python."""
    repo, baseline = repository
    _write(repo, "app/services/data/ingest/service.py")
    _git(repo, "add", ".")
    _git(repo, "commit", "--no-verify", "-m", "feature")

    decision = validation_router.route_validation(
        repo,
        profile="integration",
        base_ref=baseline,
        head_ref="HEAD",
    )

    assert decision.families == ("python",)
    assert decision.candidate.base_commit == baseline
    assert decision.candidate.head_commit == _git(repo, "rev-parse", "HEAD")


def test_mixed_ui_and_python_scope_selects_both_focused_families(
    repository: tuple[Path, str],
) -> None:
    """Disjoint known UI and Python paths produce the union of safe checks."""
    repo, _ = repository
    _write(repo, "app/services/workspace/manage_artifacts/service.py")
    _write(repo, "tests/services/workspace/manage_artifacts/test_service.py")
    _write(repo, "app/ui/src/widgets/artifacts/ArtifactsWidget.tsx")

    decision = validation_router.route_validation(repo, profile="affected")

    assert decision.families == ("python-affected", "ui-affected")
    assert decision.python_test_paths == ("tests/services/workspace/manage_artifacts",)
    assert decision.ui_test_paths == ("src/widgets/artifacts",)


def test_renamed_and_deleted_paths_are_preserved(
    repository: tuple[Path, str],
) -> None:
    """Committed impact includes deleted paths and both rename identities."""
    repo, _ = repository
    _write(repo, "docs/dev/old-name.md")
    _write(repo, "docs/dev/remove-me.md")
    _git(repo, "add", ".")
    _git(repo, "commit", "--no-verify", "-m", "fixtures")
    base = _git(repo, "rev-parse", "HEAD")
    _git(repo, "mv", "docs/dev/old-name.md", "docs/dev/new-name.md")
    _git(repo, "rm", "docs/dev/remove-me.md")
    _git(repo, "commit", "--no-verify", "-m", "move and delete")

    decision = validation_router.route_validation(
        repo,
        profile="integration",
        base_ref=base,
        head_ref="HEAD",
    )

    assert decision.changed_paths == (
        "docs/dev/new-name.md",
        "docs/dev/old-name.md",
        "docs/dev/remove-me.md",
    )
    assert decision.candidate.deleted_paths == ("docs/dev/remove-me.md",)
    assert decision.candidate.renamed_paths == (
        ("docs/dev/old-name.md", "docs/dev/new-name.md"),
    )


def test_affected_unions_committed_staged_unstaged_and_untracked(
    repository: tuple[Path, str],
) -> None:
    """Local affected discovery unions every material working-tree state."""
    repo, baseline = repository
    _write(repo, "docs/dev/committed.md")
    _git(repo, "add", ".")
    _git(repo, "commit", "--no-verify", "-m", "committed")
    _write(repo, "docs/dev/staged.md")
    _git(repo, "add", "docs/dev/staged.md")
    _write(repo, "docs/dev/unstaged.md")
    _git(repo, "add", "docs/dev/unstaged.md")
    _write(repo, "docs/dev/unstaged.md", "changed after staging\n")
    _write(repo, "docs/dev/untracked.md")

    decision = validation_router.route_validation(
        repo,
        profile="affected",
        base_ref=baseline,
        head_ref="HEAD",
    )

    assert set(decision.changed_paths) == {
        "docs/dev/committed.md",
        "docs/dev/staged.md",
        "docs/dev/unstaged.md",
        "docs/dev/untracked.md",
    }


def test_invalid_or_partial_candidate_identity_fails_closed(
    repository: tuple[Path, str],
) -> None:
    """Partial and non-commit candidate identities are rejected."""
    repo, _ = repository
    with pytest.raises(validation_router.RoutingError, match="supplied together"):
        validation_router.route_validation(
            repo, profile="affected", base_ref="HEAD", head_ref=None
        )
    with pytest.raises(validation_router.RoutingError, match="does not resolve"):
        validation_router.route_validation(
            repo,
            profile="integration",
            base_ref="missing",
            head_ref="HEAD",
        )


def test_dirty_materialized_integration_candidate_is_rejected(
    repository: tuple[Path, str],
) -> None:
    """Explicit integration evidence cannot ignore local material changes."""
    repo, baseline = repository
    _write(repo, "docs/dev/untracked.md")

    with pytest.raises(validation_router.RoutingError, match="clean"):
        validation_router.route_validation(
            repo,
            profile="integration",
            base_ref=baseline,
            head_ref="HEAD",
        )


def test_missing_integration_identity_widens_to_full(
    repository: tuple[Path, str],
) -> None:
    """An integration request without candidate refs cannot certify less."""
    repo, _ = repository

    decision = validation_router.route_validation(repo, profile="integration")

    assert decision.families == validation_router.FULL_FAMILIES
    assert decision.widened_to_full


def test_new_candidate_commit_changes_resolved_identity(
    repository: tuple[Path, str],
) -> None:
    """A later candidate cannot reuse the earlier resolved head identity."""
    repo, baseline = repository
    _write(repo, "docs/dev/first.md")
    _git(repo, "add", ".")
    _git(repo, "commit", "--no-verify", "-m", "first")
    first = validation_router.route_validation(
        repo,
        profile="integration",
        base_ref=baseline,
        head_ref="HEAD",
    )
    _write(repo, "docs/dev/second.md")
    _git(repo, "add", ".")
    _git(repo, "commit", "--no-verify", "-m", "second")
    second = validation_router.route_validation(
        repo,
        profile="integration",
        base_ref=baseline,
        head_ref="HEAD",
    )

    assert first.candidate.head_commit != second.candidate.head_commit
    assert second.changed_paths == ("docs/dev/first.md", "docs/dev/second.md")
