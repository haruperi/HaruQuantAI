"""Default fail-closed workstation owner dependencies."""

from __future__ import annotations

from collections.abc import Mapping


def unavailable_workstation_source(_: Mapping[str, object] | None = None) -> object:
    """Fail closed when no workstation owner projection is composed.

    Raises:
        RuntimeError: Always, because no owner is composed.
    """
    raise RuntimeError("WORKSTATION_PROVIDER_UNAVAILABLE")


__all__ = ("unavailable_workstation_source",)
