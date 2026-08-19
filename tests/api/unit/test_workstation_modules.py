"""Unit tests for API workstation, composition, identity, and observability modules."""

from __future__ import annotations

import importlib
import importlib.util

import pytest
from app.services.api.composition.capabilities import get_optional_capability_ids

API_TARGET_MODULES = [
    "app.services.api.widgets.dashboards.orchestration",
    "app.services.api.widgets.dashboards.schemas",
    "app.services.api.widgets.event_delivery.routes",
    "app.services.api.widgets.event_delivery.schemas",
    "app.services.api.widgets.operator.orchestration",
    "app.services.api.widgets.operator.schemas",
    "app.services.api.widgets.research.orchestration",
    "app.services.api.widgets.settings.orchestration",
    "app.services.api.widgets.settings.schemas",
    "app.services.api.widgets.watchlists.routes",
    "app.services.api.widgets.trading.routes",
    "app.services.api.widgets.indicators.schemas",
    "app.services.api.widgets.operational.routes",
    "app.services.api.composition.owner_sources",
    "app.services.api.widgets.simulation.routes",
    "app.services.api.widgets.simulation.orchestration",
    "app.services.api.composition.broker_session",
    "app.services.api.widgets.optimization.routes",
    "app.services.api.widgets.agentic.routes",
    "app.services.api.widgets.trading.orchestration",
    "app.services.api.identity.persistence.delete",
    "app.services.api.widgets.agentic.schemas",
    "app.services.api.widgets.portfolio.routes",
    "app.services.api.widgets.simulation.session_routes",
    "app.services.api.widgets.portfolio.orchestration",
    "app.services.api.widgets.watchlists.persistence.update",
    "app.services.api.composition.runtime_settings",
    "app.services.api.widgets.operational.orchestration",
    "app.services.api.widgets.event_delivery.events",
    "app.services.api.identity.persistence.update",
    "app.services.api.observability.metrics",
    "app.services.api.widgets.settings.routes",
    "app.services.api.widgets.simulation.live_routes",
    "app.services.api",
    "app.services.api.identity.authorization",
    "app.services.api.identity.routes",
]


def _absent_optional_capability(module_path: str) -> str | None:
    """Return the optional capability a module belongs to when it is absent.

    Args:
        module_path: Absolute module path under test.

    Returns:
        Owning capability identifier when absent, otherwise ``None``.
    """
    prefix = "app.services.api.widgets."
    if not module_path.startswith(prefix):
        return None
    capability_id = module_path[len(prefix) :].split(".", 1)[0]
    if capability_id not in get_optional_capability_ids():
        return None
    if importlib.util.find_spec(f"{prefix}{capability_id}") is not None:
        return None
    return capability_id


@pytest.mark.parametrize("module_path", API_TARGET_MODULES)
def test_api_target_modules_importable(module_path: str) -> None:
    """Verify every present API target module imports and initializes."""
    absent = _absent_optional_capability(module_path)
    if absent is not None:
        pytest.skip(f"optional capability absent: {absent}")
    mod = importlib.import_module(module_path)
    assert mod is not None
