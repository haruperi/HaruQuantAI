"""Secret-free trace identifier generation and validation."""

from __future__ import annotations

import hashlib
import re
import secrets
import time
import uuid

from app.kernel.errors import ValidationError

SUPPORTED_TRACE_PREFIXES = frozenset(
    {
        "brn",
        "btr",
        "cau",
        "cor",
        "evt",
        "fil",
        "led",
        "ord",
        "ply",
        "prf",
        "rbt",
        "req",
        "rpl",
        "rrn",
        "rxp",
        "scn",
        "ses",
        "wf",
    }
)
SUPPORTED_STABLE_PREFIXES = frozenset({"id"})
_STABLE_HEX = re.compile(r"[0-9a-f]{64}\Z")
_MAX_IDENTITY_MATERIAL_BYTES = 4_096
_UUID4_VERSION = 4
_UUID7_TIMESTAMP_BITS = 48
_UUID7_RANDOM_A_BITS = 12
_UUID7_RANDOM_B_BITS = 62


def _validate_trace_prefix(prefix: str) -> None:
    """Validate that the given trace prefix is supported.

    Args:
        prefix: Prefix string to validate.

    Raises:
        ValidationError: If the prefix is not in the supported set.
    """
    if prefix not in SUPPORTED_TRACE_PREFIXES:
        raise ValidationError("IDENTIFIER_PREFIX_INVALID")


def _validate_stable_prefix(prefix: str) -> None:
    """Validate that the deterministic-identity prefix is supported.

    Args:
        prefix: Prefix string to validate.

    Raises:
        ValidationError: If the prefix is not in the supported stable-ID set.
    """
    if prefix not in SUPPORTED_STABLE_PREFIXES:
        raise ValidationError("IDENTIFIER_PREFIX_INVALID")


def _validate_identifier_prefix(prefix: str) -> bool:
    """Validate and classify a supported identifier prefix.

    Args:
        prefix: Candidate trace or stable-identity prefix.

    Returns:
        True when the prefix identifies a deterministic stable ID.

    Raises:
        ValidationError: If the prefix is unsupported.
    """
    if prefix in SUPPORTED_TRACE_PREFIXES:
        _validate_trace_prefix(prefix)
        return False
    _validate_stable_prefix(prefix)
    return True


def generate_id(prefix: str) -> str:
    """Generate a canonical prefixed UUID4 identifier.

    Args:
        prefix: One of the documented UUID4 trace prefixes.

    Returns:
        A lowercase prefixed UUID4 identifier.

    Raises:
        ValidationError: If the prefix is unsupported.
    """
    _validate_trace_prefix(prefix)
    return f"{prefix}-{uuid.uuid4()}"


def generate_uuid7() -> str:
    """Generate a canonical lowercase RFC 9562 UUIDv7 string.

    UUIDv7 is used by public wire contracts whose identifiers must remain
    sortable by creation time without exposing a domain-specific prefix. The
    implementation uses the current Unix epoch millisecond in the high 48 bits,
    the RFC version/variant bits, and cryptographically strong random tail bits.

    Returns:
        Canonical lowercase UUIDv7 text.
    """
    timestamp_ms = time.time_ns() // 1_000_000
    timestamp_mask = (1 << _UUID7_TIMESTAMP_BITS) - 1
    random_a = secrets.randbits(_UUID7_RANDOM_A_BITS)
    random_b = secrets.randbits(_UUID7_RANDOM_B_BITS)
    value = (timestamp_ms & timestamp_mask) << 80
    value |= 0x7 << 76
    value |= random_a << 64
    value |= 0b10 << 62
    value |= random_b
    return str(uuid.UUID(int=value))


def validate_id(value: str, *, expected_prefix: str | None = None) -> str:
    """Validate a canonical generated or stable identifier.

    Args:
        value: Identifier to validate.
        expected_prefix: Optional required prefix.

    Returns:
        The unchanged validated identifier.

    Raises:
        ValidationError: If the prefix or syntax is invalid.
    """
    if not value or value != value.strip() or "-" not in value:
        raise ValidationError("IDENTIFIER_INVALID")
    prefix, suffix = value.split("-", 1)
    is_stable = _validate_identifier_prefix(prefix)
    if expected_prefix is not None:
        _validate_identifier_prefix(expected_prefix)
        if prefix != expected_prefix:
            raise ValidationError("IDENTIFIER_PREFIX_MISMATCH")
    if is_stable:
        if _STABLE_HEX.fullmatch(suffix) is None:
            raise ValidationError("IDENTIFIER_INVALID")
        return value
    try:
        parsed = uuid.UUID(suffix)
    except ValueError as error:
        raise ValidationError("IDENTIFIER_INVALID") from error
    if parsed.version != _UUID4_VERSION or str(parsed) != suffix:
        raise ValidationError("IDENTIFIER_INVALID")
    return value


def derive_stable_id(prefix: str, identity_material: str) -> str:
    """Derive a prefixed SHA-256 identifier from canonical material.

    Args:
        prefix: The documented non-trace ``id`` prefix.
        identity_material: Non-empty trimmed canonical Unicode material.

    Returns:
        A prefixed full lowercase SHA-256 digest.

    Raises:
        ValidationError: If the prefix or material is invalid.
    """
    _validate_stable_prefix(prefix)
    if not identity_material or identity_material != identity_material.strip():
        raise ValidationError("IDENTITY_MATERIAL_INVALID")
    encoded = identity_material.encode("utf-8")
    if len(encoded) > _MAX_IDENTITY_MATERIAL_BYTES:
        raise ValidationError("IDENTITY_MATERIAL_INVALID")
    digest = hashlib.sha256(encoded).hexdigest()
    return f"{prefix}-{digest}"
