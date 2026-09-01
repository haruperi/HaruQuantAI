"""Tests for UUIDv7 public-wire identity generation."""

import re
import uuid

from app.kernel.identity import generate_uuid7

_UUID7 = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)


def test_generate_uuid7_returns_canonical_uuid7() -> None:
    value = generate_uuid7()

    assert _UUID7.fullmatch(value) is not None
    parsed = uuid.UUID(value)
    assert parsed.version == 7
    assert parsed.variant == uuid.RFC_4122


def test_generate_uuid7_generates_distinct_values() -> None:
    assert generate_uuid7() != generate_uuid7()
