"""Strict configuration for the API and event transport feature.

Purpose:
    Parse and validate the bounded configuration accepted by
    FEAT-IFACE-SERVE_API_EVENTS.

Key capabilities:
    * Reject unknown configuration keys deterministically.
    * Pin the served API version labels and OpenAPI server prefixes.
    * Bound stream retention, replay batch size, and event payload size.

Python API usage:
    config = ServeApiEventsConfig.from_dict({"stream_retention_events": 500})

CLI usage:
    uv run python -m app.services.interfaces.serve_api_events.transport
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

_ALLOWED_CONFIG_KEYS = frozenset(
    {
        "supported_api_versions",
        "server_prefixes",
        "stream_retention_events",
        "stream_replay_batch_limit",
        "event_payload_max_bytes",
    }
)
_API_VERSION_PATTERN = re.compile(r"^v[1-9][0-9]*$")
_MAX_REPLAY_BATCH_LIMIT = 10_000


def _string_tuple(
    key: str,
    value: object,
    default: tuple[str, ...],
) -> tuple[str, ...]:
    """Normalize an optional list of non-empty strings.

    Args:
        key: Configuration key name used in error messages.
        value: Raw configuration value or None.
        default: Value returned when the key is absent.

    Returns:
        Tuple of validated non-empty strings.

    Raises:
        TypeError: If the value is not a list or tuple of non-empty strings.
    """
    if value is None:
        return default
    if isinstance(value, str) or not isinstance(value, (list, tuple)):
        message = f"{key} must be a list of strings"
        raise TypeError(message)
    for item in value:
        if not isinstance(item, str) or not item.strip():
            message = f"{key} must contain only non-empty strings"
            raise TypeError(message)
    return tuple(value)


def _bounded_int(
    key: str,
    value: object,
    default: int,
    *,
    minimum: int = 1,
    maximum: int | None = None,
) -> int:
    """Normalize an optional integer within an inclusive range.

    Args:
        key: Configuration key name used in error messages.
        value: Raw configuration value or None.
        default: Value returned when the key is absent.
        minimum: Inclusive lower bound.
        maximum: Optional inclusive upper bound.

    Returns:
        Validated integer.

    Raises:
        TypeError: If the value is not an integer.
        ValueError: If the value is outside the permitted range.
    """
    if value is None:
        return default
    if isinstance(value, bool) or not isinstance(value, int):
        message = f"{key} must be an integer"
        raise TypeError(message)
    if value < minimum:
        message = f"{key} must be at least {minimum}"
        raise ValueError(message)
    if maximum is not None and value > maximum:
        message = f"{key} must be at most {maximum}"
        raise ValueError(message)
    return value


@dataclass(frozen=True, slots=True)
class ServeApiEventsConfig:
    """Runtime configuration for the API and event transport feature.

    Attributes:
        supported_api_versions: Served API version labels such as 'v1'.
        server_prefixes: Server base paths reported by the OpenAPI manifest.
        stream_retention_events: Maximum number of retained event envelopes.
        stream_replay_batch_limit: Maximum events returned per replay batch.
        event_payload_max_bytes: Maximum serialized event payload size.
    """

    supported_api_versions: tuple[str, ...] = ("v1",)
    server_prefixes: tuple[str, ...] = ("/api/v1",)
    stream_retention_events: int = 1_000
    stream_replay_batch_limit: int = 100
    event_payload_max_bytes: int = 65_536

    def __post_init__(self) -> None:
        """Validate configuration limits and formats.

        Raises:
            ValueError: If any value is outside its documented bound.
        """
        if not self.supported_api_versions:
            message = "supported_api_versions must not be empty"
            raise ValueError(message)
        for label in self.supported_api_versions:
            if not _API_VERSION_PATTERN.match(label):
                message = "supported_api_versions entries must match 'v<N>': "
                raise ValueError(message + label)
        if not self.server_prefixes:
            message = "server_prefixes must not be empty"
            raise ValueError(message)
        for prefix in self.server_prefixes:
            if not prefix.startswith("/"):
                message = "server_prefixes entries must start with '/': "
                raise ValueError(message + prefix)
        if self.stream_retention_events < 1:
            message = "stream_retention_events must be a positive integer"
            raise ValueError(message)
        if not 1 <= self.stream_replay_batch_limit <= _MAX_REPLAY_BATCH_LIMIT:
            message = (
                "stream_replay_batch_limit must be between 1 and "
                f"{_MAX_REPLAY_BATCH_LIMIT}"
            )
            raise ValueError(message)
        if self.event_payload_max_bytes < 1:
            message = "event_payload_max_bytes must be a positive integer"
            raise ValueError(message)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> ServeApiEventsConfig:
        """Build a configuration from a mapping, rejecting unknown keys.

        Args:
            data: Configuration mapping or None for defaults.

        Returns:
            Parsed immutable configuration.

        Raises:
            ValueError: If an unknown key or an out-of-range value is present.
            TypeError: If a value has an unexpected type.
        """
        if not data:
            return cls()
        unknown = set(data) - _ALLOWED_CONFIG_KEYS
        if unknown:
            message = "Unknown serve-api-events configuration keys: " + ", ".join(
                sorted(unknown)
            )
            raise ValueError(message)
        defaults = cls()
        return cls(
            supported_api_versions=_string_tuple(
                "supported_api_versions",
                data.get("supported_api_versions"),
                defaults.supported_api_versions,
            ),
            server_prefixes=_string_tuple(
                "server_prefixes",
                data.get("server_prefixes"),
                defaults.server_prefixes,
            ),
            stream_retention_events=_bounded_int(
                "stream_retention_events",
                data.get("stream_retention_events"),
                defaults.stream_retention_events,
            ),
            stream_replay_batch_limit=_bounded_int(
                "stream_replay_batch_limit",
                data.get("stream_replay_batch_limit"),
                defaults.stream_replay_batch_limit,
                maximum=_MAX_REPLAY_BATCH_LIMIT,
            ),
            event_payload_max_bytes=_bounded_int(
                "event_payload_max_bytes",
                data.get("event_payload_max_bytes"),
                defaults.event_payload_max_bytes,
            ),
        )
