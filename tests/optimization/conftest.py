"""Shared lifecycle fixtures for focused Optimization validation."""

from collections.abc import Generator

import pytest
from app.composition.logging import shutdown_logging


@pytest.fixture(scope="session", autouse=True)
def close_optimization_test_logging() -> Generator[None]:
    """Close queued logging before pytest releases its captured streams."""
    yield
    shutdown_logging()
