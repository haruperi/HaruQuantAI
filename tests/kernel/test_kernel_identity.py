"""Unit tests for kernel identity generation and validation."""

from __future__ import annotations

import pytest
from app.kernel.errors import ValidationError
from app.kernel.identity import (
    derive_stable_id,
    generate_id,
    validate_id,
)


def test_generate_id_valid() -> None:
    """Verify generate_id produces valid prefixed UUIDv4 strings."""
    trace_id = generate_id("req")
    assert trace_id.startswith("req-")
    assert validate_id(trace_id, expected_prefix="req") == trace_id


def test_generate_id_invalid_prefix() -> None:
    """Verify generate_id rejects unsupported prefixes."""
    with pytest.raises(ValidationError, match="IDENTIFIER_PREFIX_INVALID"):
        generate_id("invalid")


def test_derive_stable_id() -> None:
    """Verify derive_stable_id produces deterministic SHA-256 digests."""
    id1 = derive_stable_id("id", "sample_material")
    id2 = derive_stable_id("id", "sample_material")
    id3 = derive_stable_id("id", "different_material")
    assert id1 == id2
    assert id1 != id3
    assert id1.startswith("id-")
    assert len(id1) == 67
    assert validate_id(id1, expected_prefix="id") == id1


def test_validate_id_mismatch() -> None:
    """Verify validate_id raises when prefix does not match expected."""
    trace_id = generate_id("req")
    with pytest.raises(ValidationError, match="IDENTIFIER_PREFIX_MISMATCH"):
        validate_id(trace_id, expected_prefix="cor")
