"""Dukascopy web-chart tick mapping tests."""

from datetime import UTC, datetime, timedelta

import pytest
from app.services.brokers.canonical_contracts.protocols import _ProviderResponseError
from app.services.brokers.dukascopy.mapping import _map_ticks

_START = datetime(2026, 1, 5, 12, tzinfo=UTC)


def test_dukascopy_mapping_preserves_genuine_values() -> None:
    """Web-chart values produce quote ticks without invented sequence data."""
    rows = ((int(_START.timestamp() * 1000), 1.1, 1.2, 2_000_000, 3_000_000),)
    ticks = _map_ticks(
        rows,
        symbol="EURUSD",
        start=_START,
        end=_START + timedelta(hours=1),
        limit=1,
    )
    assert ticks[0].provider_sequence_id is None
    assert str(ticks[0].bid) == "1.1"
    assert str(ticks[0].ask_quantity) == "3"


def test_dukascopy_mapping_rejects_malformed_row() -> None:
    """An incomplete provider row fails closed."""
    with pytest.raises(_ProviderResponseError, match="malformed Dukascopy tick row"):
        _map_ticks(
            ((1, 2),),
            symbol="EURUSD",
            start=_START,
            end=_START + timedelta(hours=1),
            limit=1,
        )


def test_dukascopy_mapping_rejects_naive_range() -> None:
    """A timezone-naive range is rejected."""
    with pytest.raises(ValueError, match="timezone-aware"):
        _map_ticks(
            (),
            symbol="EURUSD",
            start=datetime(2026, 1, 5),  # noqa: DTZ001
            end=datetime(2026, 1, 6),  # noqa: DTZ001
            limit=1,
        )
