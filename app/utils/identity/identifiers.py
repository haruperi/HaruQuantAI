"""Generate, validate, and derive secret-free trace identifiers."""

import hashlib
import re
import uuid

from app.utils.errors.exceptions import ValidationError

_SUPPORTED_PREFIXES = frozenset({"req", "wf", "cor", "cau", "evt"})
_STABLE_HEX = re.compile(r"[0-9a-f]{64}\Z")
_MAX_IDENTITY_MATERIAL_BYTES = 4_096
_UUID4_VERSION = 4


def _validate_prefix(prefix: str) -> None:
    """Validate an identifier prefix against the closed supported set.

    Args:
        prefix: Candidate prefix without a separator.

    Raises:
        ValidationError: The prefix is not supported.
    """
    if prefix not in _SUPPORTED_PREFIXES:
        raise ValidationError("IDENTIFIER_PREFIX_INVALID")


def generate_id(prefix: str) -> str:
    """Generate a canonical prefixed UUID4 identifier.

    Args:
        prefix: One of ``req``, ``wf``, ``cor``, ``cau``, or ``evt``.

    Returns:
        A lowercase identifier containing the prefix and a fresh UUID4.

    Raises:
        ValidationError: The prefix is unsupported.
    """
    _validate_prefix(prefix)
    return f"{prefix}-{uuid.uuid4()}"


def validate_id(value: str, *, expected_prefix: str | None = None) -> str:
    """Validate a canonical generated or stable identifier.

    Args:
        value: Candidate prefixed UUID4 or SHA-256 identifier.
        expected_prefix: Optional supported prefix required for this call.

    Returns:
        The unchanged canonical identifier.

    Raises:
        ValidationError: The identifier, embedded prefix, or expected prefix
            is invalid, or the prefixes do not match.
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
        prefix: Supported identifier prefix.
        identity_material: Non-empty trimmed Unicode identity material no
            larger than 4,096 UTF-8 bytes.

    Returns:
        A stable identifier containing the full lowercase SHA-256 digest.

    Raises:
        ValidationError: The prefix or identity material is invalid.
    """
    _validate_prefix(prefix)
    if not identity_material or identity_material != identity_material.strip():
        raise ValidationError("IDENTITY_MATERIAL_INVALID")
    encoded = identity_material.encode("utf-8")
    if len(encoded) > _MAX_IDENTITY_MATERIAL_BYTES:
        raise ValidationError("IDENTITY_MATERIAL_INVALID")
    return f"{prefix}-{hashlib.sha256(encoded).hexdigest()}"
