"""Unit tests for Research artifact persistence (FR-RES-097)."""

from datetime import UTC, datetime
from pathlib import Path

import pytest
from app.composition.logging import get_logger
from app.contracts.common.models import create_auth_context
from app.services.research import (
    create_research_value,
    is_research_value,
    write_research_artifact,
)

logger = get_logger(__name__)

_HASH = "e" * 64


@pytest.fixture(autouse=True)
def _stub_relational_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep unit tests isolated from Data-owned relational integration."""
    monkeypatch.setattr(
        "app.services.research.artifacts.persistence.create_artifact_metadata",
        lambda **values: values,
    )


def _report() -> object:
    """Build a canonical advisory report."""
    return create_research_value(
        "ResearchReport",
        "v1",
        "research.report.v1",
        "research-report-test",
        "Test hypothesis",
        {"data": {"rows": 1}},
        {"statistics": 7},
        _HASH,
        _HASH,
        ("fixture",),
        (),
        datetime.now(UTC),
        {"research": "v1"},
        1.0,
        True,
    )


def _auth() -> object:
    """Build a valid AuthContext."""
    return create_auth_context(
        principal_id="researcher-001",
        principal_type="USER",
        roles=("researcher",),
        permissions=("research:write",),
        scopes=("research",),
        tenant_or_environment="dev",
        request_id="req-01234567-89ab-4def-8123-456789abcdef",
        workflow_id="wf-01234567-89ab-4def-8123-456789abcdef",
        correlation_id="cor-01234567-89ab-4def-8123-456789abcdef",
        issued_at=datetime.now(UTC),
    )


def _limits() -> object:
    """Build approved resource ceilings."""
    return create_research_value("ResearchResourceLimits", 500_000, 600.0, 52_428_800)


def test_write_artifact_masks_and_replaces_atomically(tmp_path: Path) -> None:
    """FR-RES-097: artifact is masked and atomically persisted."""
    logger.debug("Testing Research artifact persistence")
    root = tmp_path / "artifacts"
    config = create_research_value("ArtifactWriteConfig", root, "json")
    destination = root / "report.json"
    ref = write_research_artifact(
        _report(), destination, config=config, auth=_auth(), limits=_limits()
    )
    assert is_research_value(ref, "ArtifactReference")
    assert ref.format == "json"
    assert ref.atomic is True
    assert ref.schema_version == "v1"
    assert ref.size_bytes > 0
    assert destination.exists()
    assert ref.relative_path.name == "report.json"


def test_write_artifact_supports_markdown_and_non_atomic_snapshot(
    tmp_path: Path,
) -> None:
    """Exercise both render formats and the explicitly non-atomic branch."""
    root = (tmp_path / "artifacts").resolve()
    markdown_config = create_research_value(
        "ArtifactWriteConfig",
        root,
        "markdown",
    )
    markdown = write_research_artifact(
        _report(),
        root / "report.md",
        config=markdown_config,
        auth=_auth(),
        limits=_limits(),
    )
    assert markdown.format == "markdown"
    assert "# Research Report" in (root / "report.md").read_text(encoding="utf-8")

    scorecard = create_research_value(
        "ResearchScorecard",
        "v1",
        ({"criterion": "metrics", "score": 20.0},),
        20.0,
        "INSUFFICIENT_EVIDENCE",
        ("score_below_review_threshold",),
        (),
        True,
    )
    snapshot = create_research_value(
        "ResearchProfileSnapshot",
        "v1",
        {"data": {"schema_version": "v1"}},
        scorecard,
        _HASH,
        _HASH,
        datetime.now(UTC),
        (),
        True,
    )
    json_config = create_research_value(
        "ArtifactWriteConfig",
        root,
        "json",
        False,
        "utf-8",
        False,
    )
    reference = write_research_artifact(
        snapshot,
        root / "snapshot.json",
        config=json_config,
        auth=_auth(),
        limits=_limits(),
    )
    assert reference.atomic is False


def test_write_artifact_fails_closed_on_path_conflict_and_size(
    tmp_path: Path,
) -> None:
    """Cover destination, traversal, conflict, and size safety gates."""
    root = (tmp_path / "artifacts").resolve()
    config = create_research_value("ArtifactWriteConfig", root, "json")
    with pytest.raises(ValueError, match="DESTINATION_NOT_ABSOLUTE"):
        write_research_artifact(
            _report(),
            Path("relative.json"),
            config=config,
            auth=_auth(),
            limits=_limits(),
        )
    with pytest.raises(PermissionError, match="ARTIFACT_PATH_TRAVERSAL"):
        write_research_artifact(
            _report(),
            tmp_path.resolve() / "outside.json",
            config=config,
            auth=_auth(),
            limits=_limits(),
        )
    destination = root / "conflict.json"
    write_research_artifact(
        _report(),
        destination,
        config=config,
        auth=_auth(),
        limits=_limits(),
    )
    with pytest.raises(ValueError, match="ARTIFACT_CONFLICT"):
        write_research_artifact(
            _report(),
            destination,
            config=config,
            auth=_auth(),
            limits=_limits(),
        )
    with pytest.raises(ValueError, match="ARTIFACT_SIZE_EXCEEDED"):
        write_research_artifact(
            _report(),
            root / "tiny.json",
            config=config,
            auth=_auth(),
            limits=create_research_value("ResearchResourceLimits", 100, 10.0, 1),
        )
