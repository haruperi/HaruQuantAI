"""Unit tests for kernel canonical JSON serialization and hashing."""

from __future__ import annotations

from decimal import Decimal

from app.kernel.serialization import (
    canonical_digest,
    canonical_json,
    to_json_safe,
)


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


def test_to_json_safe_primitives() -> None:
    """Verify to_json_safe converts complex primitives to JSON-safe representations."""
    safe = to_json_safe({"num": Decimal("100.50"), "items": (1, 2, 3)})
    assert safe == {"num": "100.50", "items": [1, 2, 3]}
