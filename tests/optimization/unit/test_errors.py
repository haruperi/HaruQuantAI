"""Tests for controlled Optimization errors."""

# ruff: noqa: INP001

import pytest
from app.services.optimization.errors import OptimizationError


def test_optimization_error_builds_redacted_payload() -> None:
    """Controlled errors expose only stable safe fields."""
    error = OptimizationError(
        "OPT_INVALID_REQUEST",
        "INVALID_PARAMETER",
        safe_details={"authorization": "secret", "field": "period"},
    )
    payload = error.to_payload()
    assert payload["code"] == "OPT_INVALID_REQUEST"
    assert payload["detail"] == "INVALID_PARAMETER"
    assert payload["details"] != {"authorization": "secret", "field": "period"}


def test_optimization_error_rejects_unknown_code() -> None:
    """Unknown codes never cross the domain boundary."""
    with pytest.raises(ValueError, match="not cataloged"):
        OptimizationError("UNKNOWN_ERROR")
