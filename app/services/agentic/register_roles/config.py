"""Strict empty configuration for the role contribution registry."""

from dataclasses import dataclass


@dataclass(frozen=True)
class RegisterRolesConfig:
    """Role contributions are request data, not feature configuration."""


def from_dict(raw: dict[str, object] | None) -> RegisterRolesConfig:
    raw = {} if raw is None else raw
    if raw:
        raise ValueError(f"unknown register-roles config keys: {sorted(raw)}")
    return RegisterRolesConfig()
