"""Unit tests for component lifecycle coordinator.

Traces to: P5-T03, Gate G5
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

import pytest
from app.kernel.effects import EffectScope
from app.kernel.errors import LifecycleError
from app.kernel.identifiers import CapabilityId
from app.kernel.lifecycle import activate_component, deactivate_component
from app.kernel.manifests import load_manifest
from app.kernel.states import ComponentState

_SAMPLE_MANIFEST = """
[provider]
id = "indicator.rsi.default"
version = "1.0.0"
entry_point = "mod:factory"

[[provides]]
capability_id = "indicator.rsi.v1"
contract_version = "1.0.0"
cardinality = "many"

[runtime]
profiles = ["research"]
scopes = ["process"]
effect_classes = ["reversible_ephemeral"]
lifecycle = "pure"
reload = "config_restart"
"""


def _dummy_factory(
    *,
    dependencies: Mapping[CapabilityId, object],
    config: Mapping[str, object],
    scope: EffectScope,
) -> str:
    del dependencies, config, scope
    return "instance"


def test_activate_component_success(tmp_path: Path) -> None:
    """Verify happy-path activation creates ActiveComponent in ACTIVE state."""
    p = tmp_path / "manifest.toml"
    p.write_text(_SAMPLE_MANIFEST.strip(), encoding="utf-8")
    manifest = load_manifest(p)

    scope = EffectScope()
    component = activate_component(
        manifest=manifest,
        factory=_dummy_factory,
        dependencies={},
        config={},
        scope=scope,
    )

    assert component.provider_id == manifest.provider_id
    assert component.state == ComponentState.ACTIVE
    assert component.instance == "instance"
    assert component.scope is scope
    assert component.scope.closed is False


def test_activate_component_failure_unwinds_partial_allocation(
    tmp_path: Path,
) -> None:
    """Verify factory failure closes effect scope and raises LifecycleError."""
    p = tmp_path / "manifest.toml"
    p.write_text(_SAMPLE_MANIFEST.strip(), encoding="utf-8")
    manifest = load_manifest(p)

    disposer_ran = False

    def _set_disposer_ran() -> None:
        nonlocal disposer_ran
        disposer_ran = True

    def _failing_factory(
        *,
        dependencies: Mapping[CapabilityId, object],
        config: Mapping[str, object],
        scope: EffectScope,
    ) -> object:
        del dependencies, config
        scope.callback(_set_disposer_ran)
        raise RuntimeError("factory failed mid-initialization")

    scope = EffectScope()
    with pytest.raises(
        LifecycleError,
        match=r"provider activation failed: indicator\.rsi\.default",
    ):
        activate_component(
            manifest=manifest,
            factory=_failing_factory,
            dependencies={},
            config={},
            scope=scope,
        )

    assert scope.closed is True
    assert disposer_ran is True


def test_deactivate_component_transitions_and_closes_scope(
    tmp_path: Path,
) -> None:
    """Verify deactivation closes scope and executes registered disposers."""
    p = tmp_path / "manifest.toml"
    p.write_text(_SAMPLE_MANIFEST.strip(), encoding="utf-8")
    manifest = load_manifest(p)

    closed_resource = False

    def _set_closed() -> None:
        nonlocal closed_resource
        closed_resource = True

    scope = EffectScope()
    scope.callback(_set_closed)

    component = activate_component(
        manifest=manifest,
        factory=_dummy_factory,
        dependencies={},
        config={},
        scope=scope,
    )

    assert closed_resource is False
    deactivate_component(component)
    assert closed_resource is True
    assert component.scope.closed is True


def test_deactivate_component_invalid_timeout_raises_value_error(
    tmp_path: Path,
) -> None:
    """Verify non-positive timeout_seconds raises ValueError."""
    p = tmp_path / "manifest.toml"
    p.write_text(_SAMPLE_MANIFEST.strip(), encoding="utf-8")
    manifest = load_manifest(p)

    component = activate_component(
        manifest=manifest,
        factory=_dummy_factory,
        dependencies={},
        config={},
        scope=EffectScope(),
    )

    with pytest.raises(ValueError, match=r"timeout_seconds must be > 0"):
        deactivate_component(component, timeout_seconds=0)

    with pytest.raises(ValueError, match=r"timeout_seconds must be > 0"):
        deactivate_component(component, timeout_seconds=-5.0)


def test_deactivate_component_is_idempotent(tmp_path: Path) -> None:
    """Verify deactivating an already deactivated component is safe and idempotent."""
    p = tmp_path / "manifest.toml"
    p.write_text(_SAMPLE_MANIFEST.strip(), encoding="utf-8")
    manifest = load_manifest(p)

    calls = 0
    scope = EffectScope()

    def _count() -> None:
        nonlocal calls
        calls += 1

    scope.callback(_count)
    component = activate_component(
        manifest=manifest,
        factory=_dummy_factory,
        dependencies={},
        config={},
        scope=scope,
    )

    deactivate_component(component)
    assert calls == 1
    deactivate_component(component)
    assert calls == 1


def test_deactivate_component_propagates_scope_error(tmp_path: Path) -> None:
    """Verify scope disposer exceptions are propagated during deactivation."""
    p = tmp_path / "manifest.toml"
    p.write_text(_SAMPLE_MANIFEST.strip(), encoding="utf-8")
    manifest = load_manifest(p)

    def _failing_disposer() -> None:
        raise RuntimeError("cleanup crash")

    scope = EffectScope()
    scope.callback(_failing_disposer)

    component = activate_component(
        manifest=manifest,
        factory=_dummy_factory,
        dependencies={},
        config={},
        scope=scope,
    )

    with pytest.raises(
        LifecycleError, match=r"effect scope cleanup failed: 1 disposer\(s\)"
    ):
        deactivate_component(component)
