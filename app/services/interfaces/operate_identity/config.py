"""Strict configuration for the account identity gateway.

Purpose:
    Parse and validate the bounded configuration accepted by
    FEAT-IFACE-OPERATE_IDENTITY.

Key capabilities:
    * Reject unknown configuration keys deterministically.
    * Specify the default principal identity when unspecified.

Python API usage:
    config = from_dict({})

CLI usage:
    uv run python -m app.services.interfaces.operate_identity.gateway
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

_ALLOWED_CONFIG_KEYS = frozenset({"default_principal"})


def from_dict(data: dict[str, Any] | None) -> OperateIdentityConfig:
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
        return OperateIdentityConfig()
    unknown = set(data) - _ALLOWED_CONFIG_KEYS
    if unknown:
        message = "Unknown operate-identity configuration keys: " + ", ".join(
            sorted(unknown)
        )
        raise ValueError(message)
    default_principal = data.get("default_principal")
    if default_principal is not None and (
        not isinstance(default_principal, str) or not default_principal.strip()
    ):
        message = "default_principal must be a non-empty string"
        raise TypeError(message)
    return OperateIdentityConfig(
        default_principal=(
            default_principal if default_principal is not None else "trader"
        ),
    )


@dataclass(frozen=True, slots=True)
class OperateIdentityConfig:
    """Runtime configuration for the identity gateway.

    Attributes:
        default_principal: Fallback principal identity when unspecified.
    """

    default_principal: str = "trader"
