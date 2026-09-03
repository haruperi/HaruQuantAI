"""Strict configuration for the account watchlist gateway.

Purpose:
    Parse and validate the bounded configuration accepted by
    FEAT-IFACE-OPERATE_WATCHLISTS.

Key capabilities:
    * Reject unknown configuration keys deterministically.
    * Pin the standalone default account until identity (G2) is ratified.

Python API usage:
    config = OperateWatchlistsConfig.from_dict({})

CLI usage:
    uv run python -m app.services.interfaces.operate_watchlists.gateway
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

_ALLOWED_CONFIG_KEYS = frozenset({"default_account_id"})


def from_dict(data: dict[str, Any] | None) -> OperateWatchlistsConfig:
    """Build a configuration from a mapping, rejecting unknown keys.

    Args:
        data: Configuration mapping or None for defaults.

    Returns:
        Parsed immutable configuration.

    Raises:
        ValueError: If an unknown key is present.
        TypeError: If a value has an unexpected type.
    """
    if not data:
        return OperateWatchlistsConfig()
    unknown = set(data) - _ALLOWED_CONFIG_KEYS
    if unknown:
        message = "Unknown operate-watchlists configuration keys: " + ", ".join(
            sorted(unknown)
        )
        raise ValueError(message)
    default_account_id = data.get("default_account_id")
    if default_account_id is not None and (
        not isinstance(default_account_id, str) or not default_account_id.strip()
    ):
        message = "default_account_id must be a non-empty string"
        raise TypeError(message)
    return OperateWatchlistsConfig(
        default_account_id=(
            default_account_id if default_account_id is not None else "local"
        ),
    )


@dataclass(frozen=True, slots=True)
class OperateWatchlistsConfig:
    """Runtime configuration for the watchlist gateway.

    Attributes:
        default_account_id: Standalone account applied to gateway
            requests until identity (G2) is ratified.
    """

    default_account_id: str = "local"
