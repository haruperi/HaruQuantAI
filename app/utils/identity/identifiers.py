"""Secret-free trace identifier generation and validation."""

from __future__ import annotations

import hashlib
import re
import uuid

from app.utils.errors.exceptions import ValidationError

SUPPORTED_PREFIXES = frozenset({"req", "wf", "cor", "cau", "evt"})
_STABLE_HEX = re.compile(r"[0-9a-f]{64}\Z")
_MAX_IDENTITY_MATERIAL_BYTES = 4_096
_UUID4_VERSION = 4


def _validate_prefix(prefix: str) -> None:
    if prefix not in SUPPORTED_PREFIXES:
        raise ValidationError("IDENTIFIER_PREFIX_INVALID")


def generate_id(prefix: str) -> str:
    """Generate a canonical prefixed UUID4 identifier.

    Args:
        prefix: One of the documented trace prefixes.

    Returns:
        A lowercase prefixed UUID4 identifier.

    Raises:
        ValidationError: If the prefix is unsupported.
    """
    _validate_prefix(prefix)
    return f"{prefix}-{uuid.uuid4()}"


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
    _validate_prefix(prefix)
    if expected_prefix is not None:
        _validate_prefix(expected_prefix)
        if prefix != expected_prefix:
            raise ValidationError("IDENTIFIER_PREFIX_MISMATCH")
    if _STABLE_HEX.fullmatch(suffix) is not None:
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
        prefix: One of the documented trace prefixes.
        identity_material: Non-empty trimmed canonical Unicode material.

    Returns:
        A prefixed full lowercase SHA-256 digest.

    Raises:
        ValidationError: If the prefix or material is invalid.
    """
    _validate_prefix(prefix)
    if not identity_material or identity_material != identity_material.strip():
        raise ValidationError("IDENTITY_MATERIAL_INVALID")
    encoded = identity_material.encode("utf-8")
    if len(encoded) > _MAX_IDENTITY_MATERIAL_BYTES:
        raise ValidationError("IDENTITY_MATERIAL_INVALID")
    digest = hashlib.sha256(encoded).hexdigest()
    return f"{prefix}-{digest}"
