"""Integration evidence for WF-RES-010: artifact persistence."""

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.services.research import (
    create_research_value,
    is_research_value,
    write_research_artifact,
)
from app.utils import create_auth_context, get_logger

logger = get_logger(__name__)

type AuthContext = Any

_HASH = "e" * 64


def _report() -> object:
    """Build a canonical advisory report."""
    return create_research_value(
        "ResearchReport",
        "v1",
        "research.report.v1",
        "research-report-int",
        "Integration test",
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
    return create_auth_context(
        contract_version="v1",
        schema_id="utils.auth_context.v1",
        principal_id="researcher-int",
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


def test_persist_masked_artifact_atomically(tmp_path: Path) -> None:
    """WF-RES-010: masked artifact is atomically persisted and audited."""
    logger.debug("Testing Research artifact persistence integration")
    root = tmp_path / "artifacts"
    config = create_research_value("ArtifactWriteConfig", root, "json")
    destination = root / "integration_report.json"
    ref = write_research_artifact(
        _report(),
        destination,
        config=config,
        auth=_auth(),
        limits=create_research_value(
            "ResearchResourceLimits", 500_000, 600.0, 52_428_800
        ),
    )
    assert is_research_value(ref, "ArtifactReference")
    assert destination.exists()
    assert ref.sha256
    assert ref.audit_event_id.startswith("evt-")
