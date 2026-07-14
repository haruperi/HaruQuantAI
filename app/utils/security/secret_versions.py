"""Immutable in-memory secret versions and explicit active selection."""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass

from pydantic import SecretStr

from app.utils.errors.exceptions import SecurityError

_VERSION = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}\Z")


@dataclass(frozen=True, slots=True)
class SecretVersion:
    """One immutable caller-supplied secret version."""

    version: str
    value: SecretStr
    active: bool = False

    def __post_init__(self) -> None:
        """Validate the public version and masked secret boundary."""
        if (
            not isinstance(self.version, str)
            or _VERSION.fullmatch(self.version) is None
        ):
            raise SecurityError("SECRET_VERSION_INVALID")
        if not isinstance(self.value, SecretStr) or not self.value.get_secret_value():
            raise SecurityError("SECRET_VERSION_INVALID")


def select_active_secret_version(
    versions: Sequence[SecretVersion],
) -> SecretVersion:
    """Select exactly one explicitly active supplied secret version.

    Args:
        versions: Immutable secret versions provided by the caller.

    Returns:
        The only version marked active.

    Raises:
        SecurityError: If entries are invalid or zero/multiple versions are active.
    """
    if not isinstance(versions, Sequence):
        raise SecurityError("SECRET_VERSION_SELECTION_INVALID")
    if any(not isinstance(version, SecretVersion) for version in versions):
        raise SecurityError("SECRET_VERSION_SELECTION_INVALID")
    active = [version for version in versions if version.active]
    if len(active) != 1:
        raise SecurityError("SECRET_VERSION_SELECTION_INVALID")
    return active[0]
