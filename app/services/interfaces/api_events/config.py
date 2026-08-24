"""Configuration model for HTTP and Event Contracts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

_ALLOWED_CONFIG_KEYS = frozenset(
    {
        "title",
        "api_version",
        "event_buffer_size",
        "max_artifact_download_bytes",
    }
)


@dataclass(frozen=True, slots=True)
class ApiEventsConfig:
    """Configuration for the HTTP and Event Contracts feature.

    Attributes:
        title: API documentation title string.
        api_version: Default API version string (e.g. 'v1').
        event_buffer_size: Maximum number of retained events in the buffer.
        max_artifact_download_bytes: Maximum allowed size in bytes per download.
    """

    title: str = "HaruQuantAI API"
    api_version: str = "v1"
    event_buffer_size: int = 1000
    max_artifact_download_bytes: int = 100 * 1024 * 1024

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> ApiEventsConfig:
        """Parse and strictly validate configuration data.

        Args:
            data: Raw configuration dictionary.

        Returns:
            Validated ApiEventsConfig instance.

        Raises:
            ValueError: If unknown keys are present or values are out of bounds.
        """
        if not data:
            return cls()

        unknown = set(data) - _ALLOWED_CONFIG_KEYS
        if unknown:
            msg = "Unknown ApiEvents configuration keys: " + ", ".join(sorted(unknown))
            raise ValueError(msg)

        title = str(data.get("title", "HaruQuantAI API"))
        api_version = str(data.get("api_version", "v1"))
        event_buffer_size = int(data.get("event_buffer_size", 1000))
        max_artifact_download_bytes = int(
            data.get("max_artifact_download_bytes", 100 * 1024 * 1024)
        )

        if event_buffer_size <= 0:
            raise ValueError("event_buffer_size must be positive")
        if max_artifact_download_bytes <= 0:
            raise ValueError("max_artifact_download_bytes must be positive")

        return cls(
            title=title,
            api_version=api_version,
            event_buffer_size=event_buffer_size,
            max_artifact_download_bytes=max_artifact_download_bytes,
        )
