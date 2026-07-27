"""Unit tests for Research artifact migrations (FR-RES-098)."""

from app.services.data import MigrationRequest
from app.services.research.artifacts import build_research_migration_request
from app.utils import logger


def test_research_migration_is_stable_and_owned() -> None:
    """FR-RES-098: migration is deterministic, owned by research."""
    logger.debug("Testing Research artifact migration")
    request = build_research_migration_request(
        "req-0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
    )
    assert isinstance(request, MigrationRequest)
    assert request.domain == "research"
    assert len(request.steps) == 1
    step = request.steps[0]
    assert step.migration_id == "001_research_artifacts_v1"
    assert step.domain == "research"
    assert step.statements
