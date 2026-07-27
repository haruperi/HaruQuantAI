"""Unit tests for market_data/symbol_metadata.py to reach >80% coverage."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from app.services.data.contracts import DataError
from app.services.data.market_data.symbol_metadata import (
    SymbolListRequest,
    SymbolMetadata,
    SymbolPage,
    VolumeRecord,
    VolumeResult,
    VolumeSummary,
    _finite,
    _unique_texts,
)

_REQ_ID = "req-11111111-1111-4111-8111-111111111111"
_NOW = datetime.now(UTC)


def test_finite_helper_invalid() -> None:
    """Test _finite helper raises ValueError on NaN."""
    with pytest.raises(ValueError, match="numeric value must be finite"):
        _finite(Decimal("NaN"))


def test_unique_texts_duplicates() -> None:
    """Test _unique_texts raises ValueError on duplicates."""
    with pytest.raises(ValueError, match="values must be unique"):
        _unique_texts(("a", "a"))


def test_symbol_list_request_invalid_limit() -> None:
    """Test SymbolListRequest raises DataError on non-positive limit."""
    with pytest.raises(DataError):
        SymbolListRequest(source_id="mt5", limit=0, request_id=_REQ_ID)


def test_symbol_page_unordered_items() -> None:
    """Test SymbolPage raises DataError when items are not sorted."""
    with pytest.raises(DataError):
        SymbolPage(
            source_id="mt5",
            items=("GBPUSD", "EURUSD"),  # Unsorted
            limit=10,
            revision="v1",
            request_id=_REQ_ID,
        )


def test_symbol_page_limit_exceeded() -> None:
    """Test SymbolPage raises DataError when len(items) > limit."""
    with pytest.raises(DataError):
        SymbolPage(
            source_id="mt5",
            items=("EURUSD", "GBPUSD"),
            limit=1,  # limit is 1, but items count is 2
            revision="v1",
            request_id=_REQ_ID,
        )


def test_symbol_metadata_invalid_digits_and_step() -> None:
    """
    Test SymbolMetadata raises DataError on negative digits or non-positive price_step.
    """
    with pytest.raises(DataError):
        SymbolMetadata(
            canonical_symbol="EURUSD",
            provider_symbol="EURUSD",
            asset_class="forex",
            source_id="mt5",
            revision="v1",
            retrieved_at=_NOW,
            digits=-1,
            request_id=_REQ_ID,
        )

    with pytest.raises(DataError):
        SymbolMetadata(
            canonical_symbol="EURUSD",
            provider_symbol="EURUSD",
            asset_class="forex",
            source_id="mt5",
            revision="v1",
            retrieved_at=_NOW,
            price_step=Decimal("-0.01"),
            request_id=_REQ_ID,
        )


def test_volume_record_negative_volume() -> None:
    """Test VolumeRecord raises DataError on negative volume."""
    with pytest.raises(DataError):
        VolumeRecord(timestamp=_NOW, volume=Decimal("-10.0"))


def test_volume_summary_min_exceeds_max() -> None:
    """Test VolumeSummary raises DataError when minimum > maximum."""
    with pytest.raises(DataError):
        VolumeSummary(
            total=Decimal(100),
            average=Decimal(50),
            minimum=Decimal(80),
            maximum=Decimal(20),  # min > max
            record_count=2,
        )


def test_volume_result_mode_mismatch() -> None:
    """Test VolumeResult raises DataError when mode='summary' but contains records."""
    v_rec = VolumeRecord(timestamp=_NOW, volume=Decimal("10.0"))
    v_sum = VolumeSummary(
        total=Decimal(10),
        average=Decimal(10),
        minimum=Decimal(10),
        maximum=Decimal(10),
        record_count=1,
    )
    with pytest.raises(DataError):
        VolumeResult(
            source_id="mt5",
            symbol="EURUSD",
            mode="summary",
            volume_kind="real",
            volume_unit="units",
            records=(v_rec,),  # Should be empty for summary mode
            summary=v_sum,
            provenance={"source": "mt5"},
            truncated=False,
            request_id=_REQ_ID,
        )
