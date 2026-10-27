"""Helper constants, bounds validation, and shared gateway for Data service."""

from __future__ import annotations

from app.host.logging import get_logger
from app.host.persistence import HostPersistence

logger = get_logger(__name__)
persistence = HostPersistence()

OVERVIEW_FR = "FR-DATAMGR-DATA-OVERVIEW"
DATASETS_CATALOG_FR = "FR-DATAMGR-DATA-CATALOG"

_MAX_CHART_ROWS = 10000


def _chart_bounds(limit: int, offset: int) -> None:
    if isinstance(limit, bool) or not 1 <= limit <= _MAX_CHART_ROWS or offset < 0:
        raise ValueError("Invalid chart pagination")


__all__ = [
    "DATASETS_CATALOG_FR",
    "OVERVIEW_FR",
    "_MAX_CHART_ROWS",
    "_chart_bounds",
    "logger",
    "persistence",
]
