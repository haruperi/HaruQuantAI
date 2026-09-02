"""Unit tests for kernel identifiers, versions, and trace IDs."""

from __future__ import annotations

import pytest
from app.kernel.errors import ValidationError
from app.kernel.identifiers import (
    CapabilityId,
    ProviderId,
    SemanticVersion,
    derive_stable_id,
    generate_id,
    validate_id,
)


def test_capability_id_parse_valid_and_str() -> None:
    """Verify CapabilityId parse and str formatting."""
    cap = CapabilityId.parse("indicator.rsi.v1")
    assert cap.domain == "indicator"
    assert cap.capability == "rsi"
    assert cap.major == 1
    assert str(cap) == "indicator.rsi.v1"


def test_capability_id_parse_invalid() -> None:
    """Verify CapabilityId raises ValueError on invalid inputs."""
    invalid_inputs = [
        123,
        "invalid",
        "a.b",
        "A.b.v1",
        "a.B.v1",
        "a.b.1",
        "a.b.v0",
        "a.b.v-1",
        "a.b.v01",
        "a.b.vabc",
    ]
    for candidate in invalid_inputs:
        with pytest.raises(ValueError, match="invalid capability id"):
            CapabilityId.parse(candidate)


def test_provider_id_parse_valid_and_str() -> None:
    """Verify ProviderId parse and str formatting."""
    prov = ProviderId.parse("indicator.rsi.default")
    assert prov.domain == "indicator"
    assert prov.capability == "rsi"
    assert prov.implementation == "default"
    assert str(prov) == "indicator.rsi.default"


def test_provider_id_parse_invalid() -> None:
    """Verify ProviderId raises ValueError on invalid inputs."""
    invalid_inputs = [
        123,
        "invalid",
        "a.b",
        "A.b.c",
        "a.B.c",
        "a.b.C",
        "a.b.c.d",
    ]
    for candidate in invalid_inputs:
        with pytest.raises(ValueError, match="invalid provider id"):
            ProviderId.parse(candidate)


def test_semantic_version_parse_valid_and_str() -> None:
    """Verify SemanticVersion parse and str formatting."""
    ver = SemanticVersion.parse("1.2.3")
    assert ver.major == 1
    assert ver.minor == 2
    assert ver.patch == 3
    assert str(ver) == "1.2.3"


def test_semantic_version_parse_invalid() -> None:
    """Verify SemanticVersion raises ValueError on invalid inputs."""
    invalid_inputs = [
        123,
        "1.2",
        "1.2.3.4",
        "1.2.x",
        "v1.2.3",
        "1.-2.3",
    ]
    for candidate in invalid_inputs:
        with pytest.raises(ValueError, match="invalid semantic version"):
            SemanticVersion.parse(candidate)


def test_generate_and_validate_id_trace_prefixes() -> None:
    """Verify generate_id and validate_id for trace prefixes."""
    trace_id = generate_id("req")
    assert trace_id.startswith("req-")
    assert validate_id(trace_id, expected_prefix="req") == trace_id

    # Invalid prefix
    with pytest.raises(ValidationError):
        generate_id("invalid_prefix")

    # Mismatched expected prefix
    with pytest.raises(ValidationError):
        validate_id(trace_id, expected_prefix="evt")

    # Malformed ID
    with pytest.raises(ValidationError):
        validate_id("invalid-not-a-uuid")
    with pytest.raises(ValidationError):
        validate_id("")
    with pytest.raises(ValidationError):
        validate_id("   req-123   ")


def test_derive_and_validate_stable_id() -> None:
    """Verify derive_stable_id and validate_id for stable prefixes."""
    stable_id = derive_stable_id("id", "canonical_content")
    assert stable_id.startswith("id-")
    assert validate_id(stable_id, expected_prefix="id") == stable_id

    # Stable id invalid material
    with pytest.raises(ValidationError):
        derive_stable_id("id", "")
    with pytest.raises(ValidationError):
        derive_stable_id("id", "   trimmed   ")
    with pytest.raises(ValidationError):
        derive_stable_id("id", "a" * 5000)
    with pytest.raises(ValidationError):
        derive_stable_id("req", "content")  # req is trace prefix, not stable prefix

    # Malformed stable ID
    with pytest.raises(ValidationError):
        validate_id("id-nothex")
