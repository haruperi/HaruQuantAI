import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum

import pytest
from app.utils import (
    ValidationError,
    canonical_digest,
    canonical_json,
    to_json_safe,
)


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


def _sha256_of_canonical(value: object) -> str:
    """Return the reference digest built from the public canonical string.

    Args:
        value: Supported value to digest.

    Returns:
        Lowercase SHA-256 hexadecimal digest of ``canonical_json(value)``.
    """
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


@pytest.mark.parametrize(
    "value",
    [
        {"b": 2, "a": 1},
        {"record": _Record(Decimal("1.2300"), _State.READY)},
        {"at": datetime(2026, 1, 1, tzinfo=UTC), "items": (1, 2, 3)},
        [{"k": index, "v": f"row-{index}"} for index in range(500)],
        {"nested": {"deep": {"rows": tuple(range(750))}}},
        "plain-string",
        [],
        {},
    ],
)
def test_canonical_digest_matches_sha256_of_canonical_json(value: object) -> None:
    """Verify the digest is byte-identical to hashing the canonical string."""
    assert canonical_digest(value) == _sha256_of_canonical(value)


def test_canonical_digest_handles_input_beyond_item_ceiling() -> None:
    """Verify the digest succeeds where canonical_json enforces its bound."""
    oversized = {"records": [{"i": index} for index in range(20_000)]}
    with pytest.raises(ValidationError):
        canonical_json(oversized)
    digest = canonical_digest(oversized)
    assert len(digest) == 64
    assert digest == canonical_digest(oversized)


def test_canonical_digest_is_order_sensitive() -> None:
    """Verify reordering sequence elements changes the digest."""
    forward = {"rows": [{"i": index} for index in range(2_000)]}
    reversed_rows = {"rows": list(reversed(forward["rows"]))}
    assert canonical_digest(forward) != canonical_digest(reversed_rows)


def test_canonical_digest_retains_safety_checks() -> None:
    """Verify the digest keeps every non-ceiling safety check."""
    with pytest.raises(ValidationError):
        canonical_digest(float("nan"))
    with pytest.raises(ValidationError):
        canonical_digest(datetime(2026, 1, 1))  # noqa: DTZ001 - naive on purpose
    cyclic: list[object] = []
    cyclic.append(cyclic)
    with pytest.raises(ValidationError):
        canonical_digest(cyclic)
