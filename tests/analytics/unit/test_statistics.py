"""Unit tests for bounded Analytics statistical validation."""

# ruff: noqa: INP001

import json
from dataclasses import replace
from pathlib import Path

import pytest
from app.services.analytics.metrics.statistics import run_statistical_validation
from app.utils import logger
from tests.analytics.unit.test_results_adapter import _config

_GOLDEN_DIRECTORY = Path("tests/analytics/fixtures/golden")


def test_statistical_validation_is_seed_reproducible() -> None:
    """An identical seed and sample produces identical real evidence."""
    logger.debug("Testing Analytics seeded statistical reproducibility")
    values = tuple(float(index - 10) for index in range(30))
    first = run_statistical_validation(values, config=_config())
    second = run_statistical_validation(values, config=_config())
    assert first == second
    assert first.status == "completed"
    for metric in first.metrics:
        fixture = json.loads(
            (_GOLDEN_DIRECTORY / f"{metric.metric_key}.json").read_text(
                encoding="utf-8"
            )
        )
        assert metric.status == fixture["expected_status"]
        if isinstance(metric.value, (tuple, float)):
            assert metric.value == pytest.approx(
                fixture["expected_value"], abs=fixture["absolute_tolerance"]
            )
        else:
            assert metric.value == fixture["expected_value"]


def test_validation_requires_configured_iteration_bounds() -> None:
    """Configured iteration excess fails closed before allocation."""
    logger.debug("Testing Analytics statistical iteration bounds")
    with pytest.raises(ValueError, match="bootstrap"):
        replace(_config(), max_bootstrap_iterations=5)


def test_statistical_validation_skips_short_sample() -> None:
    """Samples below thirty emit adequacy only and no placeholder interval."""
    logger.debug("Testing Analytics short statistical sample")
    section = run_statistical_validation((1.0, 2.0), config=_config())
    assert tuple(item.metric_key for item in section.metrics) == ("sample_adequacy",)
    assert section.status == "degraded"
