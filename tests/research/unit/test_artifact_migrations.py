"""Unit tests for Research artifact migration definitions (FR-RES-098)."""

from app.services.research import build_research_migration_request
from app.utils import get_logger

logger = get_logger(__name__)


def test_research_migration_is_stable_and_owned() -> None:
    """FR-RES-098: migration is deterministic, owned by research."""
    logger.debug("Testing Research artifact migration")
    request = build_research_migration_request(
        "req-0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
    )
    assert request.domain == "research"
    assert tuple(step.migration_id for step in request.steps) == (
        "001_research_artifacts_v1",
        "002_research_expectancy_profiles_v1",
        "003_research_governed_evidence_v1",
        "004_research_runs_v1",
    )
    assert all(step.domain == "research" for step in request.steps)
    assert all(step.statements for step in request.steps)
