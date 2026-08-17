"""Unit tests for API workstation, composition, identity, and observability modules."""

from __future__ import annotations

import importlib

import pytest

API_TARGET_MODULES = [
    "app.services.api.workstation.dashboards.orchestration",
    "app.services.api.workstation.dashboards.schemas",
    "app.services.api.workstation.event_delivery.routes",
    "app.services.api.workstation.event_delivery.schemas",
    "app.services.api.workstation.operator.orchestration",
    "app.services.api.workstation.operator.schemas",
    "app.services.api.workstation.research.orchestration",
    "app.services.api.workstation.settings.orchestration",
    "app.services.api.workstation.settings.schemas",
    "app.services.api.workstation.watchlists.routes",
    "app.services.api.workstation.trading.routes",
    "app.services.api.workstation.indicators.schemas",
    "app.services.api.workstation.operational.routes",
    "app.services.api.composition.owner_sources",
    "app.services.api.workstation.simulation.routes",
    "app.services.api.workstation.simulation.orchestration",
    "app.services.api.composition.broker_session",
    "app.services.api.workstation.optimization.routes",
    "app.services.api.workstation.agentic.routes",
    "app.services.api.workstation.trading.orchestration",
    "app.services.api.identity.persistence.delete",
    "app.services.api.workstation.agentic.schemas",
    "app.services.api.workstation.portfolio.routes",
    "app.services.api.workstation.simulation.session_routes",
    "app.services.api.workstation.portfolio.orchestration",
    "app.services.api.workstation.watchlists.persistence.update",
    "app.services.api.composition.runtime_settings",
    "app.services.api.workstation.operational.orchestration",
    "app.services.api.workstation.event_delivery.events",
    "app.services.api.identity.persistence.update",
    "app.services.api.observability.metrics",
    "app.services.api.workstation.settings.routes",
    "app.services.api.workstation.simulation.live_routes",
    "app.services.api",
    "app.services.api.identity.authorization",
    "app.services.api.identity.routes",
]


@pytest.mark.parametrize("module_path", API_TARGET_MODULES)
def test_api_target_modules_importable(module_path: str) -> None:
    """Verify all API target modules can be imported and initialized."""
    mod = importlib.import_module(module_path)
    assert mod is not None
