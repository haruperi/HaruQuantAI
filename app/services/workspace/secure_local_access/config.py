"""Strict configuration for secure local access and host protection."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.services.workspace.secure_local_access.manifest import CONFIG_KEYS

MIN_SESSION_TTL_SECONDS = 1
MAX_SESSION_TTL_SECONDS = 86400 * 7  # 7 days


@dataclass(frozen=True, slots=True)
class SecureLocalAccessConfig:
    """Strict configuration for secure local access, sessions, and host policies."""

    default_session_ttl_seconds: int = 3600
    enforce_loopback: bool = True
    allowed_remote_subnets: tuple[str, ...] = ()
    require_authenticated_remote_policy: bool = True

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any] | None,
    ) -> SecureLocalAccessConfig:
        """Parse configuration and reject unknown keys or invalid bounds.

        Args:
            data: Raw configuration dictionary.

        Returns:
            Validated SecureLocalAccessConfig instance.

        Raises:
            ValueError: If unknown keys or out-of-bound values are provided.
            TypeError: If types do not match expected schema.
        """
        if not data:
            return cls()

        unknown = set(data) - CONFIG_KEYS
        if unknown:
            keys_str = ", ".join(sorted(unknown))
            msg = f"Unknown secure-local-access configuration keys: {keys_str}"
            raise ValueError(msg)

        defaults = cls()
        ttl = data.get(
            "default_session_ttl_seconds",
            defaults.default_session_ttl_seconds,
        )
        enforce_loopback = data.get(
            "enforce_loopback",
            defaults.enforce_loopback,
        )
        allowed_subnets = data.get(
            "allowed_remote_subnets",
            defaults.allowed_remote_subnets,
        )
        require_remote = data.get(
            "require_authenticated_remote_policy",
            defaults.require_authenticated_remote_policy,
        )

        if not isinstance(ttl, int) or isinstance(ttl, bool):
            msg = "default_session_ttl_seconds must be an integer"
            raise TypeError(msg)
        if ttl < MIN_SESSION_TTL_SECONDS or ttl > MAX_SESSION_TTL_SECONDS:
            msg = (
                f"default_session_ttl_seconds must be between "
                f"{MIN_SESSION_TTL_SECONDS} and {MAX_SESSION_TTL_SECONDS}"
            )
            raise ValueError(msg)

        if not isinstance(enforce_loopback, bool):
            msg = "enforce_loopback must be a boolean"
            raise TypeError(msg)

        if not isinstance(require_remote, bool):
            msg = "require_authenticated_remote_policy must be a boolean"
            raise TypeError(msg)

        if isinstance(allowed_subnets, list | tuple):
            for subnet in allowed_subnets:
                if not isinstance(subnet, str):
                    msg = "allowed_remote_subnets must contain strings"
                    raise TypeError(msg)
            subnets_tuple = tuple(allowed_subnets)
        else:
            msg = "allowed_remote_subnets must be a sequence of strings"
            raise TypeError(msg)

        return cls(
            default_session_ttl_seconds=ttl,
            enforce_loopback=enforce_loopback,
            allowed_remote_subnets=subnets_tuple,
            require_authenticated_remote_policy=require_remote,
        )
