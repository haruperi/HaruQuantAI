"""Removal and structural boundary tests for the interfaces domain."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from app.contracts.interfaces.capabilities import SERVE_API_EVENTS_CAPABILITY
from app.kernel.capability import CapabilityUnavailableError
from app.kernel.context import DefaultFeatureContext
from app.kernel.events import EventBus
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope
from app.services.interfaces.serve_api_events.feature import feature

_ROOT = Path(__file__).resolve().parents[4]


def _load_architecture_check() -> ModuleType:
    """Load the AST architecture checker without package imports."""
    spec = importlib.util.spec_from_file_location(
        "architecture_check", _ROOT / "scripts" / "architecture_check.py"
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write(path: Path, content: str) -> None:
    """Write a synthetic module file for AST scanning."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


@pytest.mark.asyncio
async def test_capability_withdraws_on_scope_close() -> None:
    """Verify removal semantics: provider revoked, transport disposed."""
    feat = feature()
    registry = ServiceRegistry()
    scope = FeatureScope(owner_id=feat.spec.feature_id)

    def register(
        capability: Any,
        provider: Any,
        owner_scope: FeatureScope,
    ) -> None:
        registry.register(
            capability,
            provider,
            owner_id=feat.spec.feature_id,
            scope=owner_scope,
        )

    context = DefaultFeatureContext(
        spec=feat.spec,
        scope=scope,
        resolver=registry.resolve,
        provider_registrar=register,
        event_bus=EventBus(),
    )
    await feat.mount(context, None)
    assert registry.resolve(SERVE_API_EVENTS_CAPABILITY) is feat.transport

    await scope.close()
    assert registry.resolve(SERVE_API_EVENTS_CAPABILITY) is None
    with pytest.raises(CapabilityUnavailableError):
        registry.require(SERVE_API_EVENTS_CAPABILITY)


def test_real_interfaces_tree_has_no_violations() -> None:
    """Verify the shipped interfaces package passes the AST rules."""
    module = _load_architecture_check()
    violations = module.check_directory(_ROOT / "app" / "services" / "interfaces")
    assert violations == []


def test_architecture_rules_enforce_interfaces_domain(tmp_path: Path) -> None:
    """Verify init purity, feature independence, and managed tasks apply."""
    module = _load_architecture_check()
    base = tmp_path / "app" / "services" / "interfaces" / "serve_api_events"
    _write(base / "__init__.py", "VALUE = 1\n")
    _write(
        base / "boundary.py",
        "import asyncio\n"
        "from app.services.data.tick_normalization import feature\n"
        "\n"
        "\n"
        "async def start() -> None:\n"
        "    asyncio.create_task(start())\n",
    )

    violations = module.check_directory(tmp_path)
    rules = {violation.rule for violation in violations}
    assert "ARCH-001-INIT-PURITY" in rules
    assert "ARCH-002-MANAGED-TASKS" in rules
    assert "ARCH-006-FEATURE-INDEPENDENCE" in rules
