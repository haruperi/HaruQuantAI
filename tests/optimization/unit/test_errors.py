"""Tests for controlled Optimization errors."""

import pytest
from app.services.optimization.errors import (
    OPTIMIZATION_ERROR_CATALOG,
    OptimizationError,
)


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


def test_optimization_error_catalog_is_complete_and_immutable() -> None:
    """All approved Optimization codes have shared catalogue definitions."""
    expected = {
        "OPT_ADAPTER_INCOMPATIBLE",
        "OPT_CONSTRAINT_INVALID",
        "OPT_EVIDENCE_INCOMPLETE",
        "OPT_EXECUTION_FAILED",
        "OPT_INTERNAL_ERROR",
        "OPT_INVALID_REQUEST",
        "OPT_LEAKAGE_DETECTED",
        "OPT_LIMIT_EXCEEDED",
        "OPT_PERSISTENCE_FAILED",
        "OPT_STATE_CONFLICT",
    }
    assert set(OPTIMIZATION_ERROR_CATALOG) == expected
    with pytest.raises(TypeError):
        OPTIMIZATION_ERROR_CATALOG["OPT_INVALID_REQUEST"] = None  # type: ignore[index]
