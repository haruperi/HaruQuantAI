"""Unit tests for Research domain CRUD persistence operations."""

from __future__ import annotations

from app.services.research.expectancy.persistence import (
    apply_expectancy_transition,
    load_expectancy_profile,
    persist_expectancy_profile,
)
from app.services.research.persistence.create import (
    create_artifact_metadata,
    create_expectancy_profile,
)
from app.services.research.persistence.read import (
    read_approved_expectancy_profile,
    read_eligible_expectancy_profile,
    read_latest_governed_evidence,
)
from app.services.research.persistence.update import (
    update_expectancy_governance,
)


def test_research_persistence_crud_exports() -> None:
    """Verify research persistence functions can be imported."""
    assert create_artifact_metadata is not None
    assert create_expectancy_profile is not None
    assert read_approved_expectancy_profile is not None
    assert read_eligible_expectancy_profile is not None
    assert read_latest_governed_evidence is not None
    assert update_expectancy_governance is not None
    assert apply_expectancy_transition is not None
    assert load_expectancy_profile is not None
    assert persist_expectancy_profile is not None
