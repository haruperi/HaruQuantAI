from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum

import pytest
from app.utils import ValidationError, canonical_json, to_json_safe


class _State(StrEnum):
    READY = "ready"


@dataclass(frozen=True)
class _Record:
    amount: Decimal
    state: _State


def test_to_json_safe_converts_supported_types() -> None:
    result = to_json_safe(
        {
            "record": _Record(Decimal("1.2300"), _State.READY),
            "at": datetime(2026, 1, 1, tzinfo=UTC),
            "items": (1, 2),
        }
    )
    assert result == {
        "record": {"amount": "1.2300", "state": "ready"},
        "at": "2026-01-01T00:00:00.000000Z",
        "items": [1, 2],
    }


def test_canonical_json_sorts_keys() -> None:
    assert canonical_json({"b": 2, "a": 1}) == '{"a":1,"b":2}'


def test_serialization_rejects_cyclic_value() -> None:
    cyclic: list[object] = []
    cyclic.append(cyclic)
    with pytest.raises(ValidationError):
        canonical_json(cyclic)
    with pytest.raises(ValidationError):
        canonical_json(float("nan"))
