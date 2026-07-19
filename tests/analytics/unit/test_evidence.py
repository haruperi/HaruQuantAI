"""Unit tests for Analytics evidence construction and output safety."""

# ruff: noqa: INP001

import numpy as np
import pytest
from app.services.analytics import contracts
from app.services.analytics.contracts import (
    AnalyticsValidationError,
    build_quality_flag,
    build_warning,
    to_report_json_safe,
)
from app.utils import logger


def test_build_warning_bounds_detail() -> None:
    """Warning detail cannot exceed its explicit activation bound."""
    logger.debug("Testing Analytics warning bounds")
    with pytest.raises(AnalyticsValidationError):
        build_warning(
            "stop_loss_absent",
            section="trades",
            source_context="all",
            detail={"ticket": "x" * 100},
            max_detail_bytes=10,
        )


def test_build_warning_requires_configured_detail_bound() -> None:
    """Warning construction rejects a non-positive bound."""
    logger.debug("Testing Analytics warning configured bound")
    with pytest.raises(AnalyticsValidationError):
        build_warning(
            "stop_loss_absent",
            section="trades",
            source_context="all",
            detail={"ticket": "1"},
            max_detail_bytes=0,
        )


def test_quality_flag_does_not_embed_decision() -> None:
    """Quality flags contain evidence and blocker truth, not approvals."""
    logger.debug("Testing Analytics quality flag boundary")
    flag = build_quality_flag(
        "initial_balance_required",
        section="report",
        source_context="adapter",
        detail={"source_contract": "simulation.result"},
        max_detail_bytes=256,
    )
    assert flag.blocker is True
    assert "approved" not in flag.detail


def test_to_report_json_safe_rejects_infinity() -> None:
    """Non-finite NumPy values cannot cross the output boundary."""
    logger.debug("Testing Analytics finite output conversion")
    with pytest.raises(AnalyticsValidationError):
        to_report_json_safe(np.float64(np.inf))


def test_to_report_json_safe_normalizes_numpy() -> None:
    """Finite NumPy arrays become Utils-supported values."""
    logger.debug("Testing Analytics NumPy normalization")
    assert to_report_json_safe(np.array([1.0, 2.0])) == [1.0, 2.0]


def test_analytics_defines_no_utils_duplicate_primitive() -> None:
    """The contracts port does not expose duplicate Utils primitives."""
    logger.debug("Testing Analytics Utils primitive ownership boundary")
    assert "to_json_safe" not in contracts.__all__
    assert "canonical_json" not in contracts.__all__
    assert "redact_mapping_value" not in contracts.__all__
