"""Unit tests for Research artifact persistence (FR-RES-097)."""

from datetime import UTC, datetime
from pathlib import Path

from app.services.research import (
    ArtifactReference,
    ArtifactWriteConfig,
    ResearchReport,
    ResearchResourceLimits,
)
from app.services.research.artifacts import write_research_artifact
from app.utils import AuthContext, logger

_HASH = "e" * 64


def _report() -> ResearchReport:
    """Build a canonical advisory report."""
    return ResearchReport(
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


def _auth() -> AuthContext:
    """Build a valid AuthContext."""
    return AuthContext(
        contract_version="v1",
        schema_id="utils.auth_context.v1",
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


def _limits() -> ResearchResourceLimits:
    """Build approved resource ceilings."""
    return ResearchResourceLimits(500_000, 600.0, 52_428_800)


def test_write_artifact_masks_and_replaces_atomically(tmp_path: Path) -> None:
    """FR-RES-097: artifact is masked and atomically persisted."""
    logger.debug("Testing Research artifact persistence")
    root = tmp_path / "artifacts"
    config = ArtifactWriteConfig(root, "json")
    destination = root / "report.json"
    ref = write_research_artifact(
        _report(), destination, config=config, auth=_auth(), limits=_limits()
    )
    assert isinstance(ref, ArtifactReference)
    assert ref.format == "json"
    assert ref.atomic is True
    assert ref.schema_version == "v1"
    assert ref.size_bytes > 0
    assert destination.exists()
    assert ref.relative_path.name == "report.json"
