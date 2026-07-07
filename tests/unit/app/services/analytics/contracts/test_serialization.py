"""Unit tests for analytics json serialization, precision, and validation helpers."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import numpy as np
import pandas as pd
import pytest
from app.services.analytics.contracts import (
    PrecisionPolicy,
    canonical_json,
    to_json_safe,
)
from app.utils.errors import ValidationError


def test_to_json_safe_primitives() -> None:
    """Test serialization of standard primitive types."""
    policy = PrecisionPolicy()
    assert to_json_safe(None, policy) is None
    assert to_json_safe(42, policy) == 42
    assert to_json_safe(1.5, policy) == 1.5
    assert to_json_safe("hello", policy) == "hello"
    assert to_json_safe(True, policy) is True


def test_to_json_safe_nested_containers() -> None:
    """Test serialization of lists, dicts, tuples, and sets."""
    policy = PrecisionPolicy()
    payload: dict[Any, Any] = {
        123: [1, 2, (3, 4)],
        "set_data": {5, 6},
        "nested": {"key": Decimal("10.5")},
    }
    result = to_json_safe(payload, policy)
    assert isinstance(result, dict)
    assert result["123"] == [1, 2, [3, 4]]
    assert result["set_data"] == [5, 6]
    assert result["nested"] == {"key": 10.5}


def test_to_json_safe_decimal_precise_mode() -> None:
    """Test Decimal serialization with decimal_precise policy mode."""
    precise_policy = PrecisionPolicy(monetary_precision_mode="decimal_precise")
    assert to_json_safe(Decimal("100.55"), precise_policy) == "100.55"


def test_to_json_safe_rejects_non_finite() -> None:
    """Test serialization rejects non-finite float/Decimal values (ANL-NFR-433)."""
    policy = PrecisionPolicy()

    # Reject NaN / inf floats
    with pytest.raises(ValidationError) as exc_info:
        to_json_safe(float("nan"), policy)
    assert "Non-finite float" in str(exc_info.value)

    with pytest.raises(ValidationError) as exc_info:
        to_json_safe(float("inf"), policy)
    assert "Non-finite float" in str(exc_info.value)

    with pytest.raises(ValidationError) as exc_info:
        to_json_safe(float("-inf"), policy)
    assert "Non-finite float" in str(exc_info.value)

    # Reject NaN / inf Decimals
    with pytest.raises(ValidationError) as exc_info:
        to_json_safe(Decimal("NaN"), policy)
    assert "Non-finite Decimal" in str(exc_info.value)

    with pytest.raises(ValidationError) as exc_info:
        to_json_safe(Decimal("Infinity"), policy)
    assert "Non-finite Decimal" in str(exc_info.value)


def test_to_json_safe_dataclass() -> None:
    """Test custom dataclass serialization helper."""
    from dataclasses import dataclass

    @dataclass
    class DummyData:
        name: str
        value: Decimal

    policy = PrecisionPolicy()
    dummy = DummyData(name="test", value=Decimal("12.34"))
    assert to_json_safe(dummy, policy) == {"name": "test", "value": 12.34}


def test_to_json_safe_numpy_and_pandas() -> None:
    """Test numpy and pandas structures serialization when present (ANL-NFR-433)."""
    policy = PrecisionPolicy()

    if np is not None:
        arr = np.array([1, 2, 3])
        assert to_json_safe(arr, policy) == [1, 2, 3]

        scalar = np.float64(2.5)
        assert to_json_safe(scalar, policy) == 2.5

    if pd is not None:
        series = pd.Series([10, 20, 30])
        assert to_json_safe(series, policy) == [10, 20, 30]

        df = pd.DataFrame([
            {"a": 1, "b": Decimal("2.2")},
            {"a": 3, "b": Decimal("4.4")},
        ])
        assert to_json_safe(df, policy) == [
            {"a": 1, "b": 2.2},
            {"a": 3, "b": 4.4},
        ]


def test_canonical_json() -> None:
    """Test sorted, whitespace-free canonical representation (ANL-NFR-433)."""
    payload = {"c": 3, "a": 1, "b": [2, 4]}
    # canonical json sorts keys and removes all whitespaces
    result = canonical_json(payload)
    assert result == '{"a":1,"b":[2,4],"c":3}'
