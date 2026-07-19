"""Tests for Optimization public-operation validation."""

# ruff: noqa: INP001

import pytest
from app.services.optimization.public_api.validation import (
    validate_compatible_results,
    validate_request_id,
    validate_walk_forward_matrix,
)
from tests.optimization.unit.test_validation_contracts import walk_forward_request


def test_public_validation_fails_closed() -> None:
    """Blank traces, empty matrices, and empty comparisons fail before work."""
    with pytest.raises(ValueError, match="blank"):
        validate_request_id(" ")
    with pytest.raises(ValueError, match="empty"):
        validate_walk_forward_matrix((), max_requests=1)
    with pytest.raises(ValueError, match="empty"):
        validate_compatible_results(())
    assert validate_walk_forward_matrix((walk_forward_request(),), max_requests=1)
