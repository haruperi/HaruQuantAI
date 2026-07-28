"""Immutable standard response contracts for bounded public operations."""

from __future__ import annotations

import math
import re
from collections.abc import Mapping
from dataclasses import is_dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Literal, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    SerializerFunctionWrapHandler,
    field_serializer,
    field_validator,
    model_validator,
)

from app.utils.errors.metadata import normalize_error_code
from app.utils.identity.identifiers import validate_id
from app.utils.security.redaction import redact_mapping_value
from app.utils.serialization.canonical import to_json_safe

type JsonValue = (
    None | bool | int | float | str | tuple[JsonValue, ...] | Mapping[str, JsonValue]
)

_OPERATION_NAME = re.compile(r"[a-z][a-z0-9_.]{0,127}\Z")
_DOMAIN_NAME = re.compile(r"[a-z][a-z0-9_]{0,63}\Z")
_MAX_MESSAGE_LENGTH = 4_096


def _freeze_json(value: object) -> JsonValue:
    """Freeze a redacted JSON-safe value.

    Args:
        value: Redacted JSON-safe input.

    Returns:
        Recursively immutable JSON-safe data.

    Raises:
        TypeError: If the value is not JSON-safe.
        ValueError: If the value contains a non-finite number.
    """
    if value is None or isinstance(value, bool | int | str):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("metadata contains a non-finite number")
        return value
    if isinstance(value, Mapping):
        return MappingProxyType(
            {str(key): _freeze_json(nested) for key, nested in value.items()}
        )
    if isinstance(value, list | tuple):
        return tuple(_freeze_json(item) for item in value)
    raise TypeError("metadata must contain only JSON-safe values")


def _thaw_json(value: JsonValue) -> object:
    """Convert frozen JSON-safe data to ordinary serializable containers.

    Args:
        value: Frozen JSON-safe input.

    Returns:
        JSON-compatible mutable containers and scalar values.
    """
    if isinstance(value, Mapping):
        return {key: _thaw_json(nested) for key, nested in value.items()}
    if isinstance(value, tuple):
        return [_thaw_json(item) for item in value]
    return value


def _redact_and_freeze(value: Mapping[str, object]) -> Mapping[str, JsonValue]:
    """Redact and freeze one bounded metadata mapping.

    Args:
        value: Candidate metadata mapping.

    Returns:
        Immutable redacted JSON-safe metadata.

    Raises:
        TypeError: If redaction does not produce a mapping.
        ValidationError: If the mapping violates shared redaction bounds.
    """
    redacted = redact_mapping_value(value).value
    if not isinstance(redacted, Mapping):
        raise TypeError("redacted metadata must remain a mapping")
    frozen = _freeze_json(redacted)
    if not isinstance(frozen, Mapping):
        raise TypeError("frozen metadata must remain a mapping")
    return frozen


class RiskLevel(StrEnum):
    """Static invocation-risk classification for one public operation."""

    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class StandardError(BaseModel):
    """Structured, bounded, and redacted operation failure.

    Attributes:
        code: Approved symbolic error code.
        details: Bounded redacted JSON-safe diagnostic evidence.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        extra="forbid",
        frozen=True,
    )

    code: str
    details: Mapping[str, JsonValue]

    @field_validator("code")
    @classmethod
    def _validate_code(cls, value: str) -> str:
        """Validate canonical symbolic code syntax.

        Args:
            value: Candidate error code.

        Returns:
            The validated canonical code.

        Raises:
            ValueError: If the code is malformed or non-canonical.
        """
        normalized = normalize_error_code(value)
        if normalized != value:
            raise ValueError("error code must use canonical symbolic syntax")
        return value

    @field_validator("details", mode="before")
    @classmethod
    def _validate_details(cls, value: object) -> Mapping[str, JsonValue]:
        """Redact, validate, and freeze diagnostic details.

        Args:
            value: Candidate details mapping.

        Returns:
            Immutable redacted JSON-safe details.

        Raises:
            TypeError: If details are not a mapping.
            ValidationError: If details exceed shared redaction bounds.
        """
        if not isinstance(value, Mapping):
            raise TypeError("error details must be a mapping")
        return _redact_and_freeze(value)

    @field_serializer("details", when_used="json")
    def _serialize_details(self, value: Mapping[str, JsonValue]) -> object:
        """Serialize immutable details as ordinary JSON containers.

        Args:
            value: Immutable details.

        Returns:
            JSON-compatible details.
        """
        return _thaw_json(value)


class ResponseMetadata(BaseModel):
    """Required execution and side-effect metadata for a public operation.

    Attributes:
        contract_version: Shared response contract version.
        schema_id: Shared response schema identity.
        name: Stable qualified operation name.
        domain: Owning HaruQuantAI domain.
        risk_level: Static invocation-risk classification.
        request_id: Canonical request trace identifier.
        correlation_id: Optional canonical correlation identifier.
        execution_ms: Monotonic execution duration in milliseconds.
        read_only: Whether the operation has no externally observable mutation.
        writes_file: Whether the operation can write a file.
        modifies_database: Whether the operation can modify a database.
        places_trade: Whether the operation can place a trade.
        requires_network: Whether the operation can require network access.
        extensions: Preserved operation-specific envelope metadata.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        extra="forbid",
        frozen=True,
    )

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["utils.standard_response.v1"] = "utils.standard_response.v1"
    name: str
    domain: str
    risk_level: RiskLevel
    request_id: str
    correlation_id: str | None = None
    execution_ms: float
    read_only: bool
    writes_file: bool
    modifies_database: bool
    places_trade: bool
    requires_network: bool
    extensions: Mapping[str, JsonValue]

    @field_validator("name")
    @classmethod
    def _validate_name(cls, value: str) -> str:
        """Validate a stable qualified operation name.

        Args:
            value: Candidate operation name.

        Returns:
            Validated operation name.

        Raises:
            ValueError: If the name is not canonical.
        """
        if _OPERATION_NAME.fullmatch(value) is None:
            raise ValueError("name must be a lowercase qualified operation name")
        return value

    @field_validator("domain")
    @classmethod
    def _validate_domain(cls, value: str) -> str:
        """Validate a canonical domain name.

        Args:
            value: Candidate domain name.

        Returns:
            Validated domain name.

        Raises:
            ValueError: If the domain is not canonical.
        """
        if _DOMAIN_NAME.fullmatch(value) is None:
            raise ValueError("domain must be a lowercase symbolic token")
        return value

    @field_validator("request_id")
    @classmethod
    def _validate_request_id(cls, value: str) -> str:
        """Validate request trace identity.

        Args:
            value: Candidate request identifier.

        Returns:
            Validated request identifier.

        Raises:
            ValidationError: If the identifier is malformed.
        """
        return validate_id(value, expected_prefix="req")

    @field_validator("correlation_id")
    @classmethod
    def _validate_correlation_id(cls, value: str | None) -> str | None:
        """Validate optional correlation trace identity.

        Args:
            value: Candidate correlation identifier.

        Returns:
            Validated identifier or None.

        Raises:
            ValidationError: If the identifier is malformed.
        """
        if value is None:
            return None
        return validate_id(value, expected_prefix="cor")

    @field_validator("execution_ms")
    @classmethod
    def _validate_execution_ms(cls, value: float) -> float:
        """Validate rounded non-negative execution duration.

        Args:
            value: Candidate duration in milliseconds.

        Returns:
            Duration rounded to three decimal places.

        Raises:
            ValueError: If the duration is negative or non-finite.
        """
        if not math.isfinite(value) or value < 0:
            raise ValueError("execution_ms must be finite and non-negative")
        return round(value, 3)

    @field_validator("extensions", mode="before")
    @classmethod
    def _validate_extensions(cls, value: object) -> Mapping[str, JsonValue]:
        """Redact, validate, and freeze operation-specific metadata.

        Args:
            value: Candidate extension mapping.

        Returns:
            Immutable redacted JSON-safe extensions.

        Raises:
            TypeError: If extensions are not a mapping.
            ValidationError: If extensions exceed shared redaction bounds.
        """
        if not isinstance(value, Mapping):
            raise TypeError("extensions must be a mapping")
        return _redact_and_freeze(value)

    @model_validator(mode="after")
    def _validate_side_effects(self) -> Self:
        """Reject contradictory read-only and mutation declarations.

        Returns:
            The validated metadata.

        Raises:
            ValueError: If read-only is combined with a declared mutation.
        """
        if self.read_only and (
            self.writes_file or self.modifies_database or self.places_trade
        ):
            raise ValueError("read_only cannot declare a mutation side effect")
        return self

    @field_serializer("extensions", when_used="json")
    def _serialize_extensions(self, value: Mapping[str, JsonValue]) -> object:
        """Serialize immutable extensions as ordinary JSON containers.

        Args:
            value: Immutable extensions.

        Returns:
            JSON-compatible extensions.
        """
        return _thaw_json(value)


class StandardResponse[T](BaseModel):
    """Canonical result of one bounded public operation.

    The successful raw payload is stored directly in ``data``. The contract never
    inserts a ``result`` or ``payload`` wrapper around that value.

    Attributes:
        status: Function-level completion status.
        message: Bounded human-readable summary.
        data: Raw successful function result.
        error: Structured operation failure.
        metadata: Required execution, side-effect, and extension metadata.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        extra="forbid",
        frozen=True,
    )

    status: Literal["success", "error"]
    message: str
    data: T | None
    error: StandardError | None
    metadata: ResponseMetadata

    @field_serializer("data", mode="wrap", when_used="json")
    def _serialize_data(
        self,
        value: T | None,
        handler: SerializerFunctionWrapHandler,
    ) -> object:
        """Serialize immutable mapping data without changing runtime identity.

        Args:
            value: Raw operation result.
            handler: Pydantic's existing serializer for every other result type.

        Returns:
            A detached JSON-safe mapping for ``MappingProxyType`` values, or the
            existing serialized representation for every other value.

        Raises:
            ValidationError: If immutable mapping contents are unsupported,
                cyclic, unsafe, or exceed shared serialization bounds.
        """
        if isinstance(value, MappingProxyType) or (
            is_dataclass(value) and not isinstance(value, type)
        ):
            return to_json_safe(value)
        return handler(value)

    @field_validator("message")
    @classmethod
    def _validate_message(cls, value: str) -> str:
        """Validate a bounded human-readable message.

        Args:
            value: Candidate response message.

        Returns:
            Validated response message.

        Raises:
            ValueError: If the message is blank, untrimmed, or oversized.
        """
        if not value or value != value.strip() or len(value) > _MAX_MESSAGE_LENGTH:
            message = (
                "message must be a trimmed string of "
                f"1..{_MAX_MESSAGE_LENGTH} characters"
            )
            raise ValueError(message)
        return value

    @model_validator(mode="after")
    def _validate_branches(self) -> Self:
        """Validate success and error branch invariants.

        Returns:
            The validated response.

        Raises:
            ValueError: If data and error conflict with status.
        """
        if self.status == "success" and self.error is not None:
            raise ValueError("success response cannot contain an error")
        if self.status == "error" and (self.error is None or self.data is not None):
            raise ValueError("error response requires error and data=None")
        return self


__all__ = [
    "JsonValue",
    "ResponseMetadata",
    "RiskLevel",
    "StandardError",
    "StandardResponse",
]
