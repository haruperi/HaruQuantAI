"""Unit tests for the MarketDataSource abstract base protocol."""

from __future__ import annotations

import pytest
from app.services.data.sources.protocol import MarketDataSource


def test_cannot_instantiate_abstract_protocol() -> None:
    """Verify that MarketDataSource cannot be instantiated directly."""
    with pytest.raises(TypeError):
        MarketDataSource()  # type: ignore[abstract]


def test_subclass_must_implement_methods() -> None:
    """Verify that subclasses must implement abstract methods to be instantiated."""

    class IncompleteSource(MarketDataSource):
        pass

    with pytest.raises(TypeError):
        IncompleteSource()  # type: ignore[abstract]
