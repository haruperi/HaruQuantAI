"""Immutable sanitized calculation-conformance fixture contracts."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from types import MappingProxyType

_SCHEMA_ID = "brokers.calculation_fixture.v1"
_MAX_FIELDS = 32
_MAX_TEXT = 512
_SHA256_HEX_LENGTH = 64
_REQUIRED_OUTPUTS = frozenset(
    {"balance", "equity", "profit", "margin", "free_margin", "margin_level"}
)
_SENSITIVE_FRAGMENTS = ("account_id", "credential", "password", "secret", "token")


def _text(value: object, name: str, *, checksum: bool = False) -> str:
    """Validate one bounded non-empty string.

    Args:
        value: Candidate value.
        name: Stable diagnostic field name.
        checksum: Whether exactly 64 lowercase hexadecimal characters are required.

    Returns:
        Validated string.

    Raises:
        ValueError: If the value is empty, oversized, or not a checksum.
    """
    if not isinstance(value, str) or not value or len(value) > _MAX_TEXT:
        message = f"{name} must be bounded non-empty text"
        raise ValueError(message)
    if checksum and (
        len(value) != _SHA256_HEX_LENGTH
        or any(c not in "0123456789abcdef" for c in value)
    ):
        message = f"{name} must be a SHA-256 checksum"
        raise ValueError(message)
    return value


def _bounded_fields(value: Mapping[str, object], name: str) -> Mapping[str, str]:
    """Validate a bounded JSON-safe string mapping with no sensitive keys.

    Args:
        value: Candidate input or output mapping.
        name: Stable diagnostic field name.

    Returns:
        Immutable validated mapping.

    Raises:
        ValueError: If bounds, key policy, or scalar types are invalid.
    """
    if not value or len(value) > _MAX_FIELDS:
        message = f"{name} must contain 1..{_MAX_FIELDS} fields"
        raise ValueError(message)
    normalized: dict[str, str] = {}
    for key, item in value.items():
        normalized_key = _text(key, f"{name} key")
        lowered = normalized_key.lower()
        if any(fragment in lowered for fragment in _SENSITIVE_FRAGMENTS):
            message = f"{name} contains a sensitive key"
            raise ValueError(message)
        normalized[normalized_key] = _text(item, f"{name}.{normalized_key}")
    return MappingProxyType(dict(sorted(normalized.items())))


@dataclass(frozen=True, slots=True, kw_only=True)
class _CalculationFixture:
    """One checksummed provider calculation observation."""

    environment: str
    account_digest: str
    provider_specification_checksum: str
    terminal_build: str
    observed_at: datetime
    inputs: Mapping[str, str]
    outputs: Mapping[str, str]
    checksum: str = ""
    schema_id: str = _SCHEMA_ID

    def __post_init__(self) -> None:
        """Validate identity, time, sanitation, and output completeness.

        Raises:
            ValueError: If any invariant is invalid.
        """
        if self.environment not in {"demo", "simulation"}:
            raise ValueError("fixture environment must be demo or simulation")
        _text(self.account_digest, "account_digest", checksum=True)
        _text(
            self.provider_specification_checksum,
            "provider_specification_checksum",
            checksum=True,
        )
        _text(self.terminal_build, "terminal_build")
        if (
            self.observed_at.tzinfo is None
            or self.observed_at.utcoffset() != UTC.utcoffset(self.observed_at)
        ):
            raise ValueError("observed_at must be aware UTC")
        object.__setattr__(self, "inputs", _bounded_fields(self.inputs, "inputs"))
        object.__setattr__(self, "outputs", _bounded_fields(self.outputs, "outputs"))
        if not _REQUIRED_OUTPUTS.issubset(self.outputs):
            raise ValueError("fixture outputs omit projected account fields")
        if self.schema_id != _SCHEMA_ID:
            raise ValueError("fixture schema_id is unsupported")
        if self.checksum:
            _text(self.checksum, "checksum", checksum=True)


def _material(fixture: _CalculationFixture) -> dict[str, object]:
    """Return canonical JSON material excluding the checksum.

    Args:
        fixture: Validated fixture.

    Returns:
        JSON-safe canonical material.
    """
    return {
        "schema_id": fixture.schema_id,
        "environment": fixture.environment,
        "account_digest": fixture.account_digest,
        "provider_specification_checksum": fixture.provider_specification_checksum,
        "terminal_build": fixture.terminal_build,
        "observed_at": fixture.observed_at.isoformat().replace("+00:00", "Z"),
        "inputs": dict(fixture.inputs),
        "outputs": dict(fixture.outputs),
    }


def _checksum(fixture: _CalculationFixture) -> str:
    """Hash canonical fixture material.

    Args:
        fixture: Validated fixture.

    Returns:
        Lowercase SHA-256 checksum.
    """
    payload = json.dumps(_material(fixture), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_calculation_fixture(**fields: object) -> object:
    """Build and checksum one sanitized calculation fixture.

    Args:
        **fields: Complete fixture identity, input, and output fields.

    Returns:
        Opaque immutable fixture.

    Raises:
        TypeError: If fields do not satisfy the fixture types.
        ValueError: If fixture invariants are invalid.
    """
    fixture = _CalculationFixture(**fields)  # type: ignore[arg-type]
    return replace(fixture, checksum=_checksum(fixture))


def dump_calculation_fixture(value: object) -> dict[str, object]:
    """Return a verified JSON-safe fixture mapping.

    Args:
        value: Opaque calculation fixture.

    Returns:
        JSON-safe mapping including checksum.

    Raises:
        TypeError: If value is not a calculation fixture.
        ValueError: If its checksum is invalid.
    """
    if not isinstance(value, _CalculationFixture):
        raise TypeError("value must be a calculation fixture")
    if value.checksum != _checksum(value):
        raise ValueError("calculation fixture checksum mismatch")
    material = _material(value)
    material["checksum"] = value.checksum
    return material


def parse_calculation_fixture(value: Mapping[str, object]) -> object:
    """Parse and verify one canonical fixture mapping.

    Args:
        value: JSON-safe fixture mapping.

    Returns:
        Opaque immutable fixture.

    Raises:
        TypeError: If a canonical timestamp is not text.
        ValueError: If fields or checksum are invalid.
    """
    fields = dict(value)
    checksum = fields.pop("checksum", None)
    observed_at = fields.get("observed_at")
    if not isinstance(observed_at, str):
        raise TypeError("observed_at must be canonical text")
    fields["observed_at"] = datetime.fromisoformat(observed_at)
    fixture = _CalculationFixture(**fields, checksum=checksum)  # type: ignore[arg-type]
    if fixture.checksum != _checksum(fixture):
        raise ValueError("calculation fixture checksum mismatch")
    return fixture


async def collect_calculation_fixture(
    *,
    app_environment: str,
    broker_environment: str,
    account_id: str,
    provider_specification_checksum: str,
    terminal_build: str,
    observed_at: datetime,
    inputs: Mapping[str, object],
    provider_call: Callable[[], Awaitable[Mapping[str, object]]],
) -> object:
    """Collect one separately approved demo-only fixture.

    Args:
        app_environment: Application environment, required to be ``dev``.
        broker_environment: Provider environment, required to be ``demo``.
        account_id: Raw account identity used only to compute a digest.
        provider_specification_checksum: Bound specification checksum.
        terminal_build: Bound terminal build.
        observed_at: Aware-UTC observation time.
        inputs: Sanitized provider calculation inputs.
        provider_call: Explicit separately approved provider invocation.

    Returns:
        Opaque sanitized calculation fixture.

    Raises:
        PermissionError: If collection is not dev plus demo.
        ValueError: If identity or fixture evidence is invalid.
    """
    if app_environment != "dev" or broker_environment != "demo":
        raise PermissionError("fixture collection requires ENVIRONMENT=dev and demo")
    account = _text(account_id, "account_id")
    digest = hashlib.sha256(f"mt5:demo:{account}".encode()).hexdigest()
    outputs = await provider_call()
    return build_calculation_fixture(
        environment=broker_environment,
        account_digest=digest,
        provider_specification_checksum=provider_specification_checksum,
        terminal_build=terminal_build,
        observed_at=observed_at,
        inputs=inputs,
        outputs=outputs,
    )


__all__ = [
    "build_calculation_fixture",
    "collect_calculation_fixture",
    "dump_calculation_fixture",
    "parse_calculation_fixture",
]
