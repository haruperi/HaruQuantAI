"""Strategy typed-outcome tests."""

from datetime import UTC, datetime

import pytest
from app.services.strategy import (
    StrategyError,
    StrategyMutationResult,
    StrategyOutcome,
)
from app.utils import logger
from pydantic import ValidationError


def test_outcome_requires_exactly_one_branch() -> None:
    """Verify success and error branches are exclusive."""
    logger.debug("Testing Strategy outcome exclusivity")
    with pytest.raises(ValidationError):
        StrategyOutcome[str](
            status="success",
            data="ok",
            error=StrategyError(code="X", message="x", details={}),
        )


def test_strategy_error_rejects_unredacted_details() -> None:
    """Verify sensitive keys cannot enter public Strategy errors."""
    logger.debug("Testing safe Strategy error details")
    with pytest.raises(ValidationError):
        StrategyError(code="X", message="safe", details={"token": "secret"})


def test_outcome_exclusive_data_or_error() -> None:
    """Verify the documented exact outcome test name."""
    logger.debug("Testing exact Strategy outcome branch")
    test_outcome_requires_exactly_one_branch()


def test_mutation_result_has_immutable_registration_truth() -> None:
    """Verify rejected mutation truth is versioned and frozen."""
    logger.debug("Testing Strategy mutation truth")
    value = StrategyMutationResult(
        mutation_id="mut-1",
        mutation_type="REGISTER_VERSION",
        status="REJECTED",
        strategy_id="s",
        strategy_version="1",
        reason_codes=("DENIED",),
        request_id="req-1",
        correlation_id="cor-1",
        workflow_id="wf-1",
        completed_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    with pytest.raises(ValidationError):
        value.status = "ACCEPTED"
