"""Unit tests for sources/protocol.py to reach 100% coverage."""

from typing import Any

import pytest
from app.services.data.sources.protocol import MarketDataSource


class DummySource(MarketDataSource):
    """Dummy subclass that calls super abstract methods."""

    def fetch(self, request: Any) -> Any:
        return super().fetch(request)

    def list_symbols(self, request: Any) -> Any:
        return super().list_symbols(request)

    def get_symbol_metadata(self, request: Any) -> Any:
        return super().get_symbol_metadata(request)


def test_market_data_source_abstract_methods() -> None:
    """
    Test calling super() on MarketDataSource abstract methods raises NotImplementedError.
    """
    source = DummySource()

    with pytest.raises(NotImplementedError):
        source.fetch(None)

    with pytest.raises(NotImplementedError):
        source.list_symbols(None)

    with pytest.raises(NotImplementedError):
        source.get_symbol_metadata(None)
