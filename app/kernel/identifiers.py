"""Microkernel identifiers, semantic versions, and trace ID utilities."""

from __future__ import annotations

import hashlib
import re
import uuid
from dataclasses import dataclass
from typing import Self

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

_SEGMENT_RE = re.compile(r"^[a-z][a-z0-9_]*$")
_VERSION_INT_RE = re.compile(r"^(?:0|[1-9]\d*)$")


@dataclass(frozen=True, slots=True, order=True)
class CapabilityId:
    """Strongly typed capability identifier: <domain>.<capability>.v<major>."""

    domain: str
    capability: str
    major: int

    @classmethod
    def parse(cls, value: object) -> Self:
        """Parse and validate a capability ID string.

        Args:
            value: Candidate capability identifier.

        Returns:
            Validated CapabilityId instance.

        Raises:
            ValueError: If value is not a valid capability ID string.
        """
        if not isinstance(value, str):
            raise ValueError(f"invalid capability id: {value!r}")
        parts = value.split(".")
        if len(parts) != 3:
            raise ValueError(f"invalid capability id: {value!r}")
        domain, capability, major_part = parts
        if not _SEGMENT_RE.match(domain) or not _SEGMENT_RE.match(capability):
            raise ValueError(f"invalid capability id: {value!r}")
        if not major_part.startswith("v") or len(major_part) < 2:
            raise ValueError(f"invalid capability id: {value!r}")
        int_part = major_part[1:]
        if not _VERSION_INT_RE.match(int_part) or int(int_part) <= 0:
            raise ValueError(f"invalid capability id: {value!r}")
        return cls(domain=domain, capability=capability, major=int(int_part))

    def __str__(self) -> str:
        """Return the canonical string representation."""
        return f"{self.domain}.{self.capability}.v{self.major}"


@dataclass(frozen=True, slots=True, order=True)
class ProviderId:
    """Strongly typed provider identifier: <domain>.<capability>.<implementation>."""

    domain: str
    capability: str
    implementation: str

    @classmethod
    def parse(cls, value: object) -> Self:
        """Parse and validate a provider ID string.

        Args:
            value: Candidate provider identifier.

        Returns:
            Validated ProviderId instance.

        Raises:
            ValueError: If value is not a valid provider ID string.
        """
        if not isinstance(value, str):
            raise ValueError(f"invalid provider id: {value!r}")
        parts = value.split(".")
        if len(parts) != 3:
            raise ValueError(f"invalid provider id: {value!r}")
        domain, capability, implementation = parts
        if (
            not _SEGMENT_RE.match(domain)
            or not _SEGMENT_RE.match(capability)
            or not _SEGMENT_RE.match(implementation)
        ):
            raise ValueError(f"invalid provider id: {value!r}")
        return cls(domain=domain, capability=capability, implementation=implementation)

    def __str__(self) -> str:
        """Return the canonical string representation."""
        return f"{self.domain}.{self.capability}.{self.implementation}"


@dataclass(frozen=True, slots=True, order=True)
class SemanticVersion:
    """Strongly typed three-digit semantic version: <major>.<minor>.<patch>."""

    major: int
    minor: int
    patch: int

    @classmethod
    def parse(cls, value: object) -> Self:
        """Parse and validate a semantic version string.

        Args:
            value: Candidate semantic version.

        Returns:
            Validated SemanticVersion instance.

        Raises:
            ValueError: If value is not a valid semantic version string.
        """
        if not isinstance(value, str):
            raise ValueError(f"invalid semantic version: {value!r}")
        parts = value.split(".")
        if len(parts) != 3:
            raise ValueError(f"invalid semantic version: {value!r}")
        for part in parts:
            if not _VERSION_INT_RE.match(part):
                raise ValueError(f"invalid semantic version: {value!r}")
        return cls(major=int(parts[0]), minor=int(parts[1]), patch=int(parts[2]))

    def __str__(self) -> str:
        """Return the canonical string representation."""
        return f"{self.major}.{self.minor}.{self.patch}"


def _validate_trace_prefix(prefix: str) -> None:
    """Validate that the given trace prefix is supported."""
    if prefix not in SUPPORTED_TRACE_PREFIXES:
        raise ValidationError("IDENTIFIER_PREFIX_INVALID")


def _validate_stable_prefix(prefix: str) -> None:
    """Validate that the deterministic-identity prefix is supported."""
    if prefix not in SUPPORTED_STABLE_PREFIXES:
        raise ValidationError("IDENTIFIER_PREFIX_INVALID")


def _validate_identifier_prefix(prefix: str) -> bool:
    """Validate and classify a supported identifier prefix."""
    if prefix in SUPPORTED_TRACE_PREFIXES:
        _validate_trace_prefix(prefix)
        return False
    _validate_stable_prefix(prefix)
    return True


def generate_id(prefix: str) -> str:
    """Generate a canonical prefixed UUID4 identifier."""
    _validate_trace_prefix(prefix)
    return f"{prefix}-{uuid.uuid4()}"


def validate_id(value: str, *, expected_prefix: str | None = None) -> str:
    """Validate a canonical generated or stable identifier."""
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
    """Derive a prefixed SHA-256 identifier from canonical material."""
    _validate_stable_prefix(prefix)
    if not identity_material or identity_material != identity_material.strip():
        raise ValidationError("IDENTITY_MATERIAL_INVALID")
    encoded = identity_material.encode("utf-8")
    if len(encoded) > _MAX_IDENTITY_MATERIAL_BYTES:
        raise ValidationError("IDENTITY_MATERIAL_INVALID")
    digest = hashlib.sha256(encoded).hexdigest()
    return f"{prefix}-{digest}"
