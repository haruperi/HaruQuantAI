"""Test fixtures for indicators domain tests."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from app.composition.facade import bind_runtime
from app.composition.runtime import CompositionRuntime
from app.kernel.manifests import load_manifest
from app.kernel.resolver import resolve_providers
from app.services.indicators.momentum.rsi_default.plugin import (
    create_provider as rsi_factory,
)
from app.services.indicators.momentum.williams_r_default.plugin import (
    create_provider as williams_factory,
)

if TYPE_CHECKING:
    from collections.abc import Iterator

_REPO_ROOT = Path(__file__).resolve().parents[2]
_RSI_MANIFEST = (
    _REPO_ROOT
    / "app"
    / "services"
    / "indicators"
    / "momentum"
    / "rsi_default"
    / "manifest.toml"
)
_WILLIAMS_MANIFEST = (
    _REPO_ROOT
    / "app"
    / "services"
    / "indicators"
    / "momentum"
    / "williams_r_default"
    / "manifest.toml"
)


@pytest.fixture(scope="session")
def _default_indicators_runtime() -> CompositionRuntime:
    """Create a session-scoped composition runtime with default indicators providers."""
    rsi_m = load_manifest(_RSI_MANIFEST)
    w_m = load_manifest(_WILLIAMS_MANIFEST)
    report = resolve_providers(
        (rsi_m, w_m),
        enabled_provider_ids=frozenset({rsi_m.provider_id, w_m.provider_id}),
        selected_provider_ids={},
    )
    runtime = CompositionRuntime()
    runtime.activate(
        report,
        factories={
            rsi_m.provider_id: rsi_factory,
            w_m.provider_id: williams_factory,
        },
        configs={
            rsi_m.provider_id: {},
            w_m.provider_id: {},
        },
        manifests=(rsi_m, w_m),
    )
    return runtime


@pytest.fixture(autouse=True)
def _bind_default_indicators_runtime(
    request: pytest.FixtureRequest,
    _default_indicators_runtime: CompositionRuntime,
) -> Iterator[None]:
    """Auto-bind standard composition runtime for indicators tests outside providers directory."""
    if "providers" in request.node.nodeid:
        yield
        return

    with bind_runtime(_default_indicators_runtime):
        yield
