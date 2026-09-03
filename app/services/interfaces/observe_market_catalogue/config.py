"""Strict configuration for the market catalogue browsing gateway.

Purpose:
    Parse and validate the bounded configuration accepted by
    FEAT-IFACE-OBSERVE_MARKET_CATALOGUE.

Key capabilities:
    * Reject unknown configuration keys deterministically.
    * Bound catalogue page sizes.

Python API usage:
    config = ObserveMarketCatalogueConfig.from_dict({"default_page_size": 50})

CLI usage:
    uv run python -m app.services.interfaces.observe_market_catalogue.gateway
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

_ALLOWED_CONFIG_KEYS = frozenset({"default_page_size", "max_page_size"})
_MAX_PAGE_SIZE = 500


def _bounded_int(
    key: str,
    value: object,
    default: int,
) -> int:
    """Normalize an optional integer within [1, 500].

    Args:
        key: Configuration key name used in error messages.
        value: Raw configuration value or None.
        default: Value returned when the key is absent.

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
    if not 1 <= value <= _MAX_PAGE_SIZE:
        message = f"{key} must be between 1 and {_MAX_PAGE_SIZE}"
        raise ValueError(message)
    return value


@dataclass(frozen=True, slots=True)
class ObserveMarketCatalogueConfig:
    """Runtime configuration for the market catalogue gateway.

    Attributes:
        default_page_size: Page size applied when a request omits one.
        max_page_size: Upper bound applied to every requested page size.
    """

    default_page_size: int = 100
    max_page_size: int = 200

    def __post_init__(self) -> None:
        """Validate configuration limits.

        Raises:
            ValueError: If any value is outside its documented bound.
        """
        if not 1 <= self.default_page_size <= _MAX_PAGE_SIZE:
            message = f"default_page_size must be between 1 and {_MAX_PAGE_SIZE}"
            raise ValueError(message)
        if not 1 <= self.max_page_size <= _MAX_PAGE_SIZE:
            message = f"max_page_size must be between 1 and {_MAX_PAGE_SIZE}"
            raise ValueError(message)
        if self.default_page_size > self.max_page_size:
            message = "default_page_size must not exceed max_page_size"
            raise ValueError(message)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> ObserveMarketCatalogueConfig:
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
            message = (
                "Unknown observe-market-catalogue configuration keys: "
                + ", ".join(sorted(unknown))
            )
            raise ValueError(message)
        defaults = cls()
        return cls(
            default_page_size=_bounded_int(
                "default_page_size",
                data.get("default_page_size"),
                defaults.default_page_size,
            ),
            max_page_size=_bounded_int(
                "max_page_size",
                data.get("max_page_size"),
                defaults.max_page_size,
            ),
        )
