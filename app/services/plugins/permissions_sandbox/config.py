"""Strict configuration for the plugin permissions sandbox."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_HASH = re.compile(r"^[0-9a-f]{64}$")
_ENV = re.compile(r"^[A-Z_][A-Z0-9_]*$")
_MIN_PROTOCOL_BYTES = 256
_CONFIG_KEYS = frozenset(
    {
        "package_roots",
        "secret_env_names",
        "ceilings",
        "max_protocol_bytes",
        "enforcement_mode",
    }
)


@dataclass(frozen=True, slots=True)
class SandboxCeilings:
    """Feature maximums; empty permission collections mean deny."""

    filesystem_read: tuple[str, ...] = ()
    filesystem_write: tuple[str, ...] = ()
    network_endpoints: tuple[str, ...] = ()
    subprocess_allow: bool = False
    secrets: tuple[str, ...] = ()
    cpu_limit_cores: float = 1.0
    memory_limit_mb: int = 1024
    timeout_seconds: float = 60.0
    max_output_mb: int = 64


@dataclass(frozen=True, slots=True)
class SandboxPermissionsConfig:
    """Immutable process-local package and secret bindings."""

    package_roots: dict[str, Path]
    secret_env_names: dict[str, str]
    ceilings: SandboxCeilings
    max_protocol_bytes: int
    enforcement_mode: str

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> SandboxPermissionsConfig:
        """Parse configuration without filesystem or environment access.

        Args:
            data: Complete raw feature configuration mapping.

        Returns:
            Strict immutable configuration.

        Raises:
            TypeError: A value has an invalid shape.
            ValueError: A key, binding, or limit is unsafe.
        """
        if not isinstance(data, dict):
            raise TypeError("Sandbox Permissions configuration must be a mapping")
        unknown = set(data) - _CONFIG_KEYS
        if unknown:
            raise ValueError(
                "Unknown Sandbox Permissions keys: " + ", ".join(sorted(unknown))
            )
        protocol_bytes = data.get("max_protocol_bytes", 1_048_576)
        if (
            not isinstance(protocol_bytes, int)
            or isinstance(protocol_bytes, bool)
            or protocol_bytes < _MIN_PROTOCOL_BYTES
        ):
            raise ValueError("max_protocol_bytes must be an integer of at least 256")
        mode = data.get("enforcement_mode", "CURRENT_PLATFORM")
        if mode != "CURRENT_PLATFORM":
            raise ValueError("enforcement_mode must be CURRENT_PLATFORM")
        return cls(
            package_roots=_parse_roots(data.get("package_roots", {})),
            secret_env_names=_parse_secrets(data.get("secret_env_names", {})),
            ceilings=_parse_ceilings(data.get("ceilings", {})),
            max_protocol_bytes=protocol_bytes,
            enforcement_mode=mode,
        )


def _parse_roots(value: object) -> dict[str, Path]:
    """Parse package-hash bindings without resolving paths.

    Args:
        value: Raw hash-to-path mapping.

    Returns:
        Validated absolute path bindings.

    Raises:
        TypeError: The mapping or a path has the wrong type.
        ValueError: A hash or path is unsafe.
    """
    if not isinstance(value, dict):
        raise TypeError("package_roots must be a mapping")
    parsed: dict[str, Path] = {}
    for package_hash, raw_path in value.items():
        if not isinstance(package_hash, str) or not _HASH.fullmatch(package_hash):
            raise ValueError("package_roots keys must be lowercase SHA-256 hashes")
        if not isinstance(raw_path, str) or not raw_path.strip():
            raise TypeError("package root must be a non-blank string")
        path = Path(raw_path)
        if not path.is_absolute() or "\x00" in raw_path:
            raise ValueError("package root must be an absolute safe path")
        parsed[package_hash] = path
    return parsed


def _parse_secrets(value: object) -> dict[str, str]:
    """Parse SecretRef-name to host-environment-name bindings.

    Args:
        value: Raw name-to-name mapping.

    Returns:
        Validated process-local name bindings.

    Raises:
        TypeError: The supplied value is not a mapping.
        ValueError: A reference or environment name is unsafe.
    """
    if not isinstance(value, dict):
        raise TypeError("secret_env_names must be a mapping")
    parsed: dict[str, str] = {}
    for name, env_name in value.items():
        if not isinstance(name, str) or not name.strip():
            raise ValueError("SecretRef names must be non-blank strings")
        if not isinstance(env_name, str) or not _ENV.fullmatch(env_name):
            raise ValueError("secret environment names must be uppercase identifiers")
        parsed[name] = env_name
    return parsed


def _parse_ceilings(value: object) -> SandboxCeilings:
    """Parse conservative deny-by-default feature ceilings.

    Args:
        value: Raw ceiling mapping.

    Returns:
        Validated ceiling values.

    Raises:
        TypeError: A collection or scalar has the wrong type.
        ValueError: A key is unknown or a number is not positive.
    """
    if not isinstance(value, dict):
        raise TypeError("ceilings must be a mapping")
    unknown = set(value) - set(SandboxCeilings.__dataclass_fields__)
    if unknown:
        raise ValueError("Unknown sandbox ceiling keys: " + ", ".join(sorted(unknown)))
    collections = {
        name: _string_tuple(value.get(name, ()), name)
        for name in (
            "filesystem_read",
            "filesystem_write",
            "network_endpoints",
            "secrets",
        )
    }
    subprocess_allow = value.get("subprocess_allow", False)
    if not isinstance(subprocess_allow, bool):
        raise TypeError("subprocess_allow must be boolean")
    return SandboxCeilings(
        **collections,
        subprocess_allow=subprocess_allow,
        cpu_limit_cores=float(_positive(value, "cpu_limit_cores", 1.0)),
        memory_limit_mb=int(_positive(value, "memory_limit_mb", 1024)),
        timeout_seconds=float(_positive(value, "timeout_seconds", 60.0)),
        max_output_mb=int(_positive(value, "max_output_mb", 64)),
    )


def _string_tuple(value: object, name: str) -> tuple[str, ...]:
    """Return a strict tuple of non-blank strings.

    Raises:
        TypeError: The value is not a string sequence.
    """
    if not isinstance(value, (list, tuple)) or not all(
        isinstance(item, str) and item for item in value
    ):
        raise TypeError(name + " must be a sequence of non-blank strings")
    return tuple(value)


def _positive(values: dict[object, object], name: str, default: float) -> float:
    """Return one positive, non-boolean numeric ceiling.

    Raises:
        ValueError: The value is not positive numeric input.
    """
    value = values.get(name, default)
    if not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0:
        raise ValueError(name + " must be positive")
    return float(value)
