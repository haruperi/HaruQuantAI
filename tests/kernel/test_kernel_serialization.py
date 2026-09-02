"""Unit tests for kernel canonical JSON serialization and hashing."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from enum import Enum

import pytest
from app.kernel.errors import ValidationError
from app.kernel.serialization import (
    canonical_digest,
    canonical_json,
    to_json_safe,
)


class SampleEnum(Enum):
    ALPHA = "alpha_val"
    BETA = 123


@dataclass
class SampleDataclass:
    name: str
    count: int


def test_canonical_json_sorts_keys() -> None:
    """Verify canonical_json outputs sorted keys and compact formatting."""
    data = {"b": 2, "a": 1, "nested": {"z": 10, "y": 20}}
    json_str = canonical_json(data)
    assert json_str == '{"a":1,"b":2,"nested":{"y":20,"z":10}}'


def test_canonical_digest_stable() -> None:
    """Verify canonical_digest generates stable 64-char SHA-256 digests."""
    data = {"symbol": "EURUSD", "volume": Decimal("1.5")}
    digest1 = canonical_digest(data)
    digest2 = canonical_digest({"volume": Decimal("1.5"), "symbol": "EURUSD"})
    assert digest1 == digest2
    assert len(digest1) == 64


def test_to_json_safe_primitives_and_types() -> None:
    """Verify to_json_safe converts complex primitives to JSON-safe representations."""
    dt = datetime(2026, 9, 1, 12, 0, 0, tzinfo=UTC)
    safe = to_json_safe(
        {
            "num": Decimal("100.50"),
            "items": (1, 2, 3),
            "enum1": SampleEnum.ALPHA,
            "enum2": SampleEnum.BETA,
            "dc": SampleDataclass(name="test", count=5),
            "dt": dt,
            "flag": True,
            "none_val": None,
        }
    )
    assert safe == {
        "num": "100.50",
        "items": [1, 2, 3],
        "enum1": "alpha_val",
        "enum2": 123,
        "dc": {"name": "test", "count": 5},
        "dt": "2026-09-01T12:00:00.000000Z",
        "flag": True,
        "none_val": None,
    }


def test_serialization_datetime_validation() -> None:
    """Verify naive and non-UTC datetimes are rejected."""
    naive = datetime(2026, 9, 1, 12, 0, 0)  # noqa: DTZ001
    with pytest.raises(ValidationError, match="SERIALIZATION_DATETIME_INVALID"):
        to_json_safe(naive)

    non_utc = datetime(2026, 9, 1, 12, 0, 0, tzinfo=timezone(timedelta(hours=5)))
    with pytest.raises(ValidationError, match="SERIALIZATION_DATETIME_INVALID"):
        to_json_safe(non_utc)


def test_serialization_non_finite_numbers() -> None:
    """Verify inf and NaN floats and decimals are rejected."""
    with pytest.raises(ValidationError, match="SERIALIZATION_NON_FINITE"):
        to_json_safe(float("inf"))
    with pytest.raises(ValidationError, match="SERIALIZATION_NON_FINITE"):
        to_json_safe(float("nan"))
    with pytest.raises(ValidationError, match="SERIALIZATION_NON_FINITE"):
        to_json_safe(Decimal("Infinity"))


def test_serialization_cycle_detection() -> None:
    """Verify cycles in lists and dicts raise ValidationError."""
    lst: list[object] = []
    lst.append(lst)
    with pytest.raises(ValidationError, match="SERIALIZATION_CYCLE_DETECTED"):
        to_json_safe(lst)

    dct: dict[str, object] = {}
    dct["self"] = dct
    with pytest.raises(ValidationError, match="SERIALIZATION_CYCLE_DETECTED"):
        to_json_safe(dct)


def test_serialization_depth_and_items_limits() -> None:
    """Verify depth and item count limits are enforced."""
    nested: object = 1
    for _ in range(35):
        nested = [nested]
    with pytest.raises(ValidationError, match="SERIALIZATION_DEPTH_EXCEEDED"):
        to_json_safe(nested)

    large_list = list(range(10_005))
    with pytest.raises(ValidationError, match="SERIALIZATION_ITEMS_EXCEEDED"):
        to_json_safe(large_list)


def test_serialization_invalid_keys_and_unsupported_types() -> None:
    """Verify non-string keys and unsupported types raise ValidationError."""
    with pytest.raises(ValidationError, match="SERIALIZATION_KEY_INVALID"):
        to_json_safe({123: "value"})

    with pytest.raises(ValidationError, match="SERIALIZATION_TYPE_UNSUPPORTED"):
        to_json_safe({1, 2, 3})  # Set is unsupported
