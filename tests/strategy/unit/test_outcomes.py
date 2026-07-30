"""Strategy StandardResponse contract tests."""

from datetime import UTC, datetime

import pytest
from app.services.strategy.contracts import StrategyMutationResult
from app.utils import generate_id, get_logger
from app.utils.responses.models import (
    ResponseMetadata,
    RiskLevel,
    StandardError,
    StandardResponse,
)
from pydantic import ValidationError

logger = get_logger(__name__)


def _metadata() -> ResponseMetadata:
    """Build minimal valid response metadata for contract tests."""
    return ResponseMetadata(
        name="strategy.test",
        domain="strategy",
        risk_level=RiskLevel.LOW,
        request_id=generate_id("req"),
        correlation_id=generate_id("cor"),
        execution_ms=0.001,
        read_only=True,
        writes_file=False,
        modifies_database=False,
        places_trade=False,
        requires_network=False,
        extensions={},
    )


def test_response_requires_exclusive_error_branch() -> None:
    """Verify StandardResponse success and error branches are exclusive."""
    logger.debug("Testing Strategy response exclusivity")
    with pytest.raises(ValidationError):
        StandardResponse[str](
            status="success",
            message="ok",
            data="ok",
            error=StandardError(code="STRATEGY_INVALID_CONFIG", details={}),
            metadata=_metadata(),
        )


def test_strategy_error_details_are_redacted() -> None:
    """Verify sensitive values cannot cross the shared error contract."""
    logger.debug("Testing safe Strategy error details")
    value = StandardError(code="STRATEGY_INVALID_CONFIG", details={"token": "secret"})
    assert "secret" not in str(value.details)


def test_outcome_exclusive_data_or_error() -> None:
    """Retain the historical test name for the migrated response rule."""
    test_response_requires_exclusive_error_branch()


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
