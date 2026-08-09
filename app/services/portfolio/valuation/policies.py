"""Versioned valuation source policy helpers."""

from __future__ import annotations

from collections.abc import Mapping


def select_price(
    position: Mapping[str, object], policy: Mapping[str, object]
) -> tuple[object | None, str]:
    """Select a side-aware price or preserve unknown evidence.

    Returns:
        Selected price and declared source name.
    """
    side = str(position.get("side", "long"))
    source = str(
        policy.get("long_source" if side == "long" else "short_source", "mark")
    )
    return position.get(source), source


__all__ = ("select_price",)
