"""Unit tests for API workstation, composition, identity, and observability modules."""

from __future__ import annotations

import importlib

import pytest

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


@pytest.mark.parametrize("module_path", API_TARGET_MODULES)
def test_api_target_modules_importable(module_path: str) -> None:
    """Verify all API target modules can be imported and initialized."""
    mod = importlib.import_module(module_path)
    assert mod is not None
