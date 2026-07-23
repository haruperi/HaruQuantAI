"""Unit tests for synthetic generation."""

from datetime import UTC, datetime

import pytest
from app.services.data.contracts import DataError
from app.services.data.synthetic_data.contracts import SyntheticRequest
from app.services.data.synthetic_data.gbm import (
    SYNTHETIC_BAR_MAX_RECORDS,
    SYNTHETIC_TICK_MAX_RECORDS,
    generate_synthetic_dataset,
)


def test_synthetic_dataset_replays_from_seed() -> None:
    """Test synthetic dataset GBM generation is deterministic when using same seed."""
    req1 = SyntheticRequest(
        symbol="BTC/USD",
        data_kind="bars",
        timeframe="M1",
        start=datetime(2026, 7, 1, 12, 0, tzinfo=UTC),
        record_count=10,
        method="gbm",
        parameters={"mu": 0.05, "sigma": 0.2, "start_val": 100.0},
        seed=42,
        precision_policy="decimal_string",
        request_id="req-9456bdfa12ea76959c94a3572f5d91c73d838622df0a8d9b4e815c276c6b7880",
    )

    req2 = SyntheticRequest(
        symbol="BTC/USD",
        data_kind="bars",
        timeframe="M1",
        start=datetime(2026, 7, 1, 12, 0, tzinfo=UTC),
        record_count=10,
        method="gbm",
        parameters={"mu": 0.05, "sigma": 0.2, "start_val": 100.0},
        seed=42,
        precision_policy="decimal_string",
        request_id="req-a697f8b99a46c8465b9a70e7af44e49a7665cf1ce8e62c3b42678f1c26b21814",
    )

    ds1 = generate_synthetic_dataset(req1)
    ds2 = generate_synthetic_dataset(req2)

    assert ds1.record_count == 10
    assert len(ds1.records) == 10
    assert ds1.records[0].open == ds2.records[0].open
    assert ds1.records[-1].close == ds2.records[-1].close


def test_synthetic_ticks_generation() -> None:
    """Test synthetic tick generation from GBM path."""
    req = SyntheticRequest(
        symbol="BTC/USD",
        data_kind="ticks",
        timeframe=None,
        start=datetime(2026, 7, 1, 12, 0, tzinfo=UTC),
        record_count=10,
        method="gbm",
        parameters={"mu": 0.05, "sigma": 0.2, "start_val": 100.0},
        seed=42,
        precision_policy="decimal_string",
        request_id="req-0b43c1e5a01f391ad6257f03d5af3bc5d3b78394cfe4aa9d5d3dbcbc1b4d8a2d",
    )
    ds = generate_synthetic_dataset(req)
    assert ds.data_kind == "ticks"
    assert ds.record_count == 10
    assert len(ds.records) == 10


def test_synthetic_dataset_limit_exceeded() -> None:
    """Test that exceed limits raises LIMIT_EXCEEDED."""
    req_bar = SyntheticRequest(
        symbol="BTC/USD",
        data_kind="bars",
        timeframe="M1",
        start=datetime(2026, 7, 1, 12, 0, tzinfo=UTC),
        record_count=SYNTHETIC_BAR_MAX_RECORDS + 1,
        method="gbm",
        parameters={"mu": 0.05, "sigma": 0.2, "start_val": 100.0},
        seed=42,
        precision_policy="decimal_string",
        request_id="req-9456bdfa12ea76959c94a3572f5d91c73d838622df0a8d9b4e815c276c6b7880",
    )

    with pytest.raises(DataError) as exc_info:
        generate_synthetic_dataset(req_bar)
    assert exc_info.value.args[0] == "LIMIT_EXCEEDED"

    req_tick = SyntheticRequest(
        symbol="BTC/USD",
        data_kind="ticks",
        timeframe=None,
        start=datetime(2026, 7, 1, 12, 0, tzinfo=UTC),
        record_count=SYNTHETIC_TICK_MAX_RECORDS + 1,
        method="gbm",
        parameters={"mu": 0.05, "sigma": 0.2, "start_val": 100.0},
        seed=42,
        precision_policy="decimal_string",
        request_id="req-a697f8b99a46c8465b9a70e7af44e49a7665cf1ce8e62c3b42678f1c26b21814",
    )

    with pytest.raises(DataError) as exc_info:
        generate_synthetic_dataset(req_tick)
    assert exc_info.value.args[0] == "LIMIT_EXCEEDED"


def test_synthetic_invalid_parameters() -> None:
    """Test validation errors for invalid parameters."""
    # Missing mu
    req = SyntheticRequest(
        symbol="BTC/USD",
        data_kind="bars",
        timeframe="M1",
        start=datetime(2026, 7, 1, 12, 0, tzinfo=UTC),
        record_count=10,
        method="gbm",
        parameters={"sigma": 0.2, "start_val": 100.0},
        seed=42,
        precision_policy="decimal_string",
        request_id="req-9456bdfa12ea76959c94a3572f5d91c73d838622df0a8d9b4e815c276c6b7880",
    )
    with pytest.raises(DataError) as exc_info:
        generate_synthetic_dataset(req)
    assert exc_info.value.args[0] == "INVALID_INPUT"

    # Non-positive sigma
    req2 = SyntheticRequest(
        symbol="BTC/USD",
        data_kind="bars",
        timeframe="M1",
        start=datetime(2026, 7, 1, 12, 0, tzinfo=UTC),
        record_count=10,
        method="gbm",
        parameters={"mu": 0.05, "sigma": -0.2, "start_val": 100.0},
        seed=42,
        precision_policy="decimal_string",
        request_id="req-a697f8b99a46c8465b9a70e7af44e49a7665cf1ce8e62c3b42678f1c26b21814",
    )
    with pytest.raises(DataError) as exc_info:
        generate_synthetic_dataset(req2)
    assert exc_info.value.args[0] == "INVALID_INPUT"

    # Missing timeframe for bars

    with pytest.raises(DataError):
        SyntheticRequest(
            symbol="BTC/USD",
            data_kind="bars",
            timeframe=None,
            start=datetime(2026, 7, 1, 12, 0, tzinfo=UTC),
            record_count=10,
            method="gbm",
            parameters={"mu": 0.05, "sigma": 0.2, "start_val": 100.0},
            seed=42,
            precision_policy="decimal_string",
            request_id="req-bc0e142195cb27a6127a29283e0ccdfb3a51449da848f04abee1c1526184084e",
        )
