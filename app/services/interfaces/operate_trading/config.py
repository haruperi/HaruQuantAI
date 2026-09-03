"""Strict configuration for the governed trading gateway.

Purpose:
    Parse and validate the bounded configuration accepted by
    FEAT-IFACE-OPERATE_TRADING.

Key capabilities:
    * Reject unknown configuration keys deterministically.
    * Pin default account and safety boundaries.

Python API usage:
    config = OperateTradingConfig.from_dict({})
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

_ALLOWED_CONFIG_KEYS = frozenset({"default_account_id", "max_order_quantity"})


def from_dict(data: dict[str, Any] | None) -> OperateTradingConfig:
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
        return OperateTradingConfig()
    unknown = set(data) - _ALLOWED_CONFIG_KEYS
    if unknown:
        message = "Unknown operate-trading configuration keys: " + ", ".join(
            sorted(unknown)
        )
        raise ValueError(message)
    default_account_id = data.get("default_account_id")
    if default_account_id is not None and (
        not isinstance(default_account_id, str) or not default_account_id.strip()
    ):
        message = "default_account_id must be a non-empty string"
        raise TypeError(message)
    max_order_quantity = data.get("max_order_quantity")
    if max_order_quantity is not None and not isinstance(
        max_order_quantity, (int, float)
    ):
        message = "max_order_quantity must be a number"
        raise TypeError(message)

    return OperateTradingConfig(
        default_account_id=(
            default_account_id if default_account_id is not None else "default"
        ),
        max_order_quantity=(
            float(max_order_quantity) if max_order_quantity is not None else 1000.0
        ),
    )


@dataclass(frozen=True, slots=True)
class OperateTradingConfig:
    """Runtime configuration for the trading operations gateway.

    Attributes:
        default_account_id: Default account identifier.
        max_order_quantity: Hard ceiling on single-order quantities.
    """

    default_account_id: str = "default"
    max_order_quantity: float = 1000.0
