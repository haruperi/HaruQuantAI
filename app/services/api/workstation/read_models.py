"""Versioned operational workstation projection."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime


def build_workstation_read_model(
    *,
    version: int,
    as_of: datetime,
    panels: Mapping[str, object],
    freshness: Mapping[str, object],
) -> Mapping[str, object]:
    """Build a bounded read model preserving unknown panel values.

    Returns:
        Versioned operational workstation projection.
    """
    projected = {
        name: panels.get(name, {"status": "unknown", "reason": "PROVIDER_UNAVAILABLE"})
        for name in (
            "market",
            "portfolio",
            "trade",
            "planning",
            "warnings",
            "emergency",
            "training",
        )
    }
    return {
        "schema": "OperationalWorkstation",
        "contract_version": "v1",
        "version": version,
        "as_of": as_of.isoformat(),
        "freshness": dict(freshness),
        "panels": projected,
    }
