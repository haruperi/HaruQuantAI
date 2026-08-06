"""Coverage expansion tests for strategy/signals/_mechanics.py."""

from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from app.services.strategy.signals._mechanics import (
    _bar_records,
    _decimal_parameter,
    _feature_values,
    _integer_parameter,
    _parameter,
    _related_market,
    _SignalConfigError,
    _SignalDataError,
    _text_parameter,
)


def test_parameter_readers_validation() -> None:
    """Verify strategy parameter reading and error handling."""
    config = MagicMock()
    config.normalized_parameters = {
        "int_val": 10,
        "bool_val": True,
        "str_int": "10",
        "dec_val": "12.34",
        "nan_val": "NaN",
        "text_val": "  hello  ",
        "empty_text": "   ",
    }

    # Missing parameter
    with pytest.raises(_SignalConfigError, match="missing required parameter"):
        _parameter(config, "missing_key")

    # Integer parameter type check
    assert _integer_parameter(config, "int_val") == 10
    with pytest.raises(_SignalConfigError, match="parameter must be an integer"):
        _integer_parameter(config, "bool_val")
    with pytest.raises(_SignalConfigError, match="parameter must be an integer"):
        _integer_parameter(config, "str_int")

    # Decimal parameter type & finiteness check
    assert _decimal_parameter(config, "dec_val") == Decimal("12.34")
    with pytest.raises(_SignalConfigError, match="parameter must be numeric"):
        _decimal_parameter(config, "bool_val")
    with pytest.raises(
        _SignalConfigError, match="parameter must be decimal-compatible"
    ):
        _decimal_parameter(config, "text_val")
    with pytest.raises(_SignalConfigError, match="parameter must be finite"):
        _decimal_parameter(config, "nan_val")

    # Text parameter non-empty check
    assert _text_parameter(config, "text_val") == "hello"
    with pytest.raises(_SignalConfigError, match="parameter must be non-empty text"):
        _text_parameter(config, "empty_text")
    with pytest.raises(_SignalConfigError, match="parameter must be non-empty text"):
        _text_parameter(config, "int_val")


def test_data_readers_validation() -> None:
    """Verify _bar_records, _related_market, and _feature_values error handling."""
    market = MagicMock()
    market.data_kind = "ticks"  # Not 'bars'
    market.records = (MagicMock(),)

    # _bar_records data_kind check
    with pytest.raises(
        _SignalDataError, match="signal evaluation requires non-empty bar data"
    ):
        _bar_records(market)

    # _bar_records non-OHLCVRecord check
    market.data_kind = "bars"
    market.records = ("not-a-record",)
    with pytest.raises(
        _SignalDataError, match="signal evaluation requires canonical OHLCV records"
    ):
        _bar_records(market)

    # _related_market missing check
    evidence = MagicMock()
    evidence.related_markets = {}
    with pytest.raises(_SignalDataError, match="missing related market"):
        _related_market(evidence, "EURUSD")

    # _feature_values missing/too short check
    evidence.features = {"feat1": (Decimal("1.0"),)}
    with pytest.raises(_SignalDataError):
        _feature_values(evidence, "missing_feat", minimum=1)
    with pytest.raises(_SignalDataError):
        _feature_values(evidence, "feat1", minimum=5)


def test_indicator_and_series_mechanics() -> None:
    """Verify indicator reading and series mechanics."""
    import numpy as np
    from app.services.strategy.signals._mechanics import (
        _current_previous,
        _current_value,
        _indicator_reference,
        _indicator_values,
        _position_tag,
        _ready_indicator_values,
        _SignalIndicatorError,
    )

    # Indicator mock
    ind1 = MagicMock()
    ind1.indicator_id = "sma_14"
    ind1.output_columns = ("sma",)
    ind1.values = {"sma": np.array([10.0, 11.0, 12.0])}
    ind1.manifest.output_checksum = "chk-123"

    indicators = (ind1,)

    # _indicator_values
    vals = _indicator_values(indicators, indicator_id="sma_14", output_column="sma")
    assert vals == (10.0, 11.0, 12.0)

    # Missing indicator -> raises _SignalIndicatorError
    with pytest.raises(_SignalIndicatorError):
        _indicator_values(indicators, indicator_id="missing", output_column="sma")

    # _ready_indicator_values
    ready = _ready_indicator_values(
        indicators, indicator_id="sma_14", output_column="sma", minimum=2
    )
    assert ready == (Decimal("10.0"), Decimal("11.0"), Decimal("12.0"))

    # Insufficient ready count -> raises _SignalIndicatorError
    with pytest.raises(_SignalIndicatorError):
        _ready_indicator_values(
            indicators, indicator_id="sma_14", output_column="sma", minimum=10
        )

    # _indicator_reference
    assert (
        _indicator_reference(indicators, indicator_id="sma_14", output_column="sma")
        == "chk-123"
    )

    # _current_previous and _current_value
    curr, prev = _current_previous((10.0, 12.0), "sma")
    assert curr == Decimal("12.0")
    assert prev == Decimal("10.0")

    with pytest.raises(_SignalIndicatorError):
        _current_previous((10.0,), "sma")

    with pytest.raises(_SignalIndicatorError):
        _current_previous((10.0, float("nan")), "sma")

    assert _current_value((10.0, 12.0), "sma") == Decimal("12.0")

    with pytest.raises(_SignalIndicatorError):
        _current_value((), "sma")

    # _position_tag
    assert _position_tag(12345, "BUY") == "mt5-magic:12345:BUY"


def test_make_signal_construction() -> None:
    """Verify _make_signal builds active/inactive signals and validates side."""
    from datetime import UTC, datetime

    from app.services.data import build_ohlcv_record
    from app.services.strategy.signals._mechanics import _make_signal

    evaluator = MagicMock(strategy_id="str-1", strategy_version="1.0.0")
    config = MagicMock(config_hash="cfg-hash")
    context = MagicMock(workflow_id="wf-1")

    now = datetime.now(UTC)
    bar = build_ohlcv_record(
        timestamp=now,
        source="test",
        source_symbol="EURUSD",
        available_at=now,
        open=Decimal(10),
        high=Decimal(12),
        low=Decimal(9),
        close=Decimal(11),
        volume=Decimal(100),
        price_unit="USD",
        volume_unit="units",
    )
    market = MagicMock(data_kind="bars", symbol="EURUSD", records=(bar,))
    evidence = MagicMock(evidence_id="ev-1", primary_market=market)

    # Invalid side
    with pytest.raises(_SignalConfigError, match="signal side must be BUY or SELL"):
        _make_signal(
            evaluator,
            evidence,
            config,
            context,
            signal_name="sig",
            side="HOLD",
            active=True,
        )

    # Valid signal
    sig = _make_signal(
        evaluator, evidence, config, context, signal_name="sig", side="BUY", active=True
    )
    assert sig.strategy_id == "str-1"
    assert sig.symbol == "EURUSD"
    assert sig.side == "BUY"
    assert sig.active is True


def test_indicator_exception_handling_propagation() -> None:
    """Verify focused test doubles fallback on TypeError/AttributeError and propagate RuntimeError."""
    from unittest.mock import patch

    from app.services.strategy.signals._mechanics import (
        _indicator_frame,
        _indicator_metadata,
    )

    # 1. Focused test double with values/manifest falls back correctly
    double = MagicMock()
    double.indicator_id = "test_ind"
    double.output_columns = ("col1",)
    double.manifest.output_checksum = "checksum-123"
    double.values = {"col1": [1.0, 2.0]}

    meta = _indicator_metadata(double)
    assert meta["indicator_id"] == "test_ind"
    assert meta["manifest"]["output_checksum"] == "checksum-123"

    frame = _indicator_frame(double)
    assert frame == {"col1": [1.0, 2.0]}

    # 2. TypeError and AttributeError take the compatibility fallback path
    mock_obj = object()
    with (
        patch(
            "app.services.strategy.signals._mechanics._get_indicator_metadata",
            side_effect=TypeError("Not an indicator"),
        ),
        pytest.raises(AttributeError),
    ):
        _indicator_metadata(mock_obj)

    # 3. Unexpected exception (e.g. RuntimeError) propagates instead of being hidden
    with (
        patch(
            "app.services.strategy.signals._mechanics._get_indicator_metadata",
            side_effect=RuntimeError("Unexpected internal failure"),
        ),
        pytest.raises(RuntimeError, match="Unexpected internal failure"),
    ):
        _indicator_metadata(mock_obj)

    with (
        patch(
            "app.services.strategy.signals._mechanics._get_indicator_values",
            side_effect=RuntimeError("Unexpected getter failure"),
        ),
        pytest.raises(RuntimeError, match="Unexpected getter failure"),
    ):
        _indicator_frame(mock_obj)
