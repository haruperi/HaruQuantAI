"""Analytics Workbench gateway feature (FEAT-API-28).

Owns the read-mostly Analytics gateway behind ``/api/v1/analytics``:
catalogue discovery, attached report reads, the delegated workbench
projection, trade pagination, comparison delegation, and metadata-only
annotations and archive transitions.
"""

from app.services.api.workstation.analytics_workbench.orchestration import (
    build_analytics_workbench_source,
    build_analytics_workbench_source_bundle,
)

__all__ = (
    "build_analytics_workbench_source",
    "build_analytics_workbench_source_bundle",
)
