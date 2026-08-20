"""Unit tests for configuration reconciliation and generational rollback.

Traces to: P6-T03, Gate G6
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from app.composition.reconciliation import (
    ProviderConfiguration,
    reconcile_configuration,
)
from app.composition.runtime import CompositionRuntime
from app.kernel.discovery import discover_manifests
from app.kernel.errors import ManifestValidationError
from app.kernel.identifiers import CapabilityId, ProviderId
from app.kernel.registry import build_inventory
from app.kernel.resolver import resolve_providers

if TYPE_CHECKING:
    from collections.abc import Mapping

    from app.kernel.effects import EffectScope

_MANIFEST_RSI_1 = """
[provider]
id = "indicator.rsi.p1"
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

_MANIFEST_RSI_2 = """
[provider]
id = "indicator.rsi.p2"
version = "2.0.0"
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


def test_reconcile_noop_returns_empty_result(tmp_path: Path) -> None:
    """Verify reconciling identical configuration performs no activations."""
    p1_path = tmp_path / "rsi1" / "manifest.toml"
    p1_path.parent.mkdir()
    p1_path.write_text(_MANIFEST_RSI_1.strip(), encoding="utf-8")

    discovered = discover_manifests(tmp_path)
    inventory = build_inventory(discovered)

    p1 = ProviderId.parse("indicator.rsi.p1")
    cfg = ProviderConfiguration(
        enabled_provider_ids=frozenset([p1]),
        selected_provider_ids={},
        provider_configs={p1: {"period": 14}},
    )

    runtime = CompositionRuntime()
    factories = {
        p1: lambda *, dependencies, config, scope: f"rsi_p1_{config.get('period')}"
    }

    # Initial activation
    rep = resolve_providers(
        inventory.providers,
        enabled_provider_ids=cfg.enabled_provider_ids,
        selected_provider_ids=cfg.selected_provider_ids,
    )
    runtime.activate(rep, factories=factories, configs=cfg.provider_configs)

    # Reconcile same config
    res = reconcile_configuration(runtime, inventory, cfg, cfg, factories=factories)
    assert res.changed_provider_ids == ()
    assert res.activated_generation_ids == ()
    assert res.rolled_back is False


def test_reconcile_selection_switch_yields_new_generation_and_lease(
    tmp_path: Path,
) -> None:
    """Verify switching provider selections deactivates incumbent and binds new generation."""
    (tmp_path / "p1").mkdir()
    (tmp_path / "p1" / "manifest.toml").write_text(
        _MANIFEST_RSI_1.strip(), encoding="utf-8"
    )
    (tmp_path / "p2").mkdir()
    (tmp_path / "p2" / "manifest.toml").write_text(
        _MANIFEST_RSI_2.strip(), encoding="utf-8"
    )

    discovered = discover_manifests(tmp_path)
    inventory = build_inventory(discovered)

    p1 = ProviderId.parse("indicator.rsi.p1")
    p2 = ProviderId.parse("indicator.rsi.p2")
    c_rsi = CapabilityId.parse("indicator.rsi.v1")

    factories = {
        p1: lambda *, dependencies, config, scope: "instance_p1",
        p2: lambda *, dependencies, config, scope: "instance_p2",
    }

    # Config 1: select p1
    cfg1 = ProviderConfiguration(
        enabled_provider_ids=frozenset([p1, p2]),
        selected_provider_ids={c_rsi: p1},
    )

    runtime = CompositionRuntime()
    rep1 = resolve_providers(
        inventory.providers,
        enabled_provider_ids=cfg1.enabled_provider_ids,
        selected_provider_ids=cfg1.selected_provider_ids,
    )
    runtime.activate(rep1, factories=factories, configs={})
    lease1 = runtime.lease(c_rsi)
    assert lease1.instance == "instance_p1"

    # Config 2: select p2
    cfg2 = ProviderConfiguration(
        enabled_provider_ids=frozenset([p1, p2]),
        selected_provider_ids={c_rsi: p2},
    )

    res = reconcile_configuration(runtime, inventory, cfg1, cfg2, factories=factories)
    assert res.rolled_back is False
    assert set(res.changed_provider_ids) == {p1, p2}

    lease2 = runtime.lease(c_rsi)
    assert lease2.instance == "instance_p2"
    assert lease2.generation_id != lease1.generation_id


def test_reconcile_config_digest_change_updates_generation(
    tmp_path: Path,
) -> None:
    """Verify changing config values creates a new generation with new digest."""
    (tmp_path / "p1").mkdir()
    (tmp_path / "p1" / "manifest.toml").write_text(
        _MANIFEST_RSI_1.strip(), encoding="utf-8"
    )

    discovered = discover_manifests(tmp_path)
    inventory = build_inventory(discovered)
    p1 = ProviderId.parse("indicator.rsi.p1")
    c_rsi = CapabilityId.parse("indicator.rsi.v1")

    def _factory(
        *,
        dependencies: Mapping[CapabilityId, object],
        config: Mapping[str, object],
        scope: EffectScope,
    ) -> str:
        del dependencies, scope
        return f"rsi_{config.get('period')}"

    factories = {p1: _factory}

    cfg1 = ProviderConfiguration(
        enabled_provider_ids=frozenset([p1]),
        provider_configs={p1: {"period": 14}},
    )
    runtime = CompositionRuntime()
    rep1 = resolve_providers(
        inventory.providers,
        enabled_provider_ids=cfg1.enabled_provider_ids,
        selected_provider_ids={},
    )
    runtime.activate(rep1, factories=factories, configs=cfg1.provider_configs)
    assert runtime.lease(c_rsi).instance == "rsi_14"

    cfg2 = ProviderConfiguration(
        enabled_provider_ids=frozenset([p1]),
        provider_configs={p1: {"period": 21}},
    )
    res = reconcile_configuration(runtime, inventory, cfg1, cfg2, factories=factories)
    assert res.rolled_back is False
    assert res.changed_provider_ids == (p1,)
    assert runtime.lease(c_rsi).instance == "rsi_21"


def test_reconcile_candidate_failure_rolls_back_and_preserves_incumbent(
    tmp_path: Path,
) -> None:
    """Verify failure during candidate activation rolls back and restores incumbent."""
    (tmp_path / "p1").mkdir()
    (tmp_path / "p1" / "manifest.toml").write_text(
        _MANIFEST_RSI_1.strip(), encoding="utf-8"
    )
    (tmp_path / "p2").mkdir()
    (tmp_path / "p2" / "manifest.toml").write_text(
        _MANIFEST_RSI_2.strip(), encoding="utf-8"
    )

    discovered = discover_manifests(tmp_path)
    inventory = build_inventory(discovered)
    p1 = ProviderId.parse("indicator.rsi.p1")
    p2 = ProviderId.parse("indicator.rsi.p2")
    c_rsi = CapabilityId.parse("indicator.rsi.v1")

    def _failing_p2(
        *,
        dependencies: Mapping[CapabilityId, object],
        config: Mapping[str, object],
        scope: EffectScope,
    ) -> str:
        del dependencies, config, scope
        raise RuntimeError("p2 crashed on startup")

    factories = {
        p1: lambda *, dependencies, config, scope: "instance_p1",
        p2: _failing_p2,
    }

    cfg1 = ProviderConfiguration(
        enabled_provider_ids=frozenset([p1]),
        selected_provider_ids={c_rsi: p1},
    )
    runtime = CompositionRuntime()
    rep1 = resolve_providers(
        inventory.providers,
        enabled_provider_ids=cfg1.enabled_provider_ids,
        selected_provider_ids=cfg1.selected_provider_ids,
    )
    runtime.activate(rep1, factories=factories, configs={})
    assert runtime.lease(c_rsi).instance == "instance_p1"

    # Candidate attempts to switch to p2 which fails
    cfg2 = ProviderConfiguration(
        enabled_provider_ids=frozenset([p1, p2]),
        selected_provider_ids={c_rsi: p2},
    )
    res = reconcile_configuration(runtime, inventory, cfg1, cfg2, factories=factories)
    assert res.rolled_back is True
    # Incumbent p1 is restored
    assert runtime.lease(c_rsi).instance == "instance_p1"


def test_reconcile_uninstalled_provider_raises_manifest_validation_error(
    tmp_path: Path,
) -> None:
    """Verify referencing an uninstalled provider raises ManifestValidationError."""
    discovered = discover_manifests(tmp_path)
    inventory = build_inventory(discovered)

    p_uninstalled = ProviderId.parse("uninstalled.provider.default")
    cfg = ProviderConfiguration(
        enabled_provider_ids=frozenset([p_uninstalled]),
    )

    runtime = CompositionRuntime()
    with pytest.raises(ManifestValidationError, match=r"provider is not installed"):
        reconcile_configuration(
            runtime, inventory, ProviderConfiguration(), cfg, factories={}
        )


def test_gate_g6_switches_consumer_to_new_generation_without_retaining_stale_instance(
    tmp_path: Path,
) -> None:
    """Gate G6: Switch provider configuration and assert new generation is bound."""
    (tmp_path / "p1").mkdir()
    (tmp_path / "p1" / "manifest.toml").write_text(
        _MANIFEST_RSI_1.strip(), encoding="utf-8"
    )

    discovered = discover_manifests(tmp_path)
    inventory = build_inventory(discovered)
    p1 = ProviderId.parse("indicator.rsi.p1")
    c_rsi = CapabilityId.parse("indicator.rsi.v1")

    count = 0

    def _factory(
        *,
        dependencies: Mapping[CapabilityId, object],
        config: Mapping[str, object],
        scope: EffectScope,
    ) -> str:
        del dependencies, config, scope
        nonlocal count
        count += 1
        return f"instance_gen_{count}"

    runtime = CompositionRuntime()
    cfg1 = ProviderConfiguration(
        enabled_provider_ids=frozenset([p1]),
        provider_configs={p1: {"v": 1}},
    )
    rep1 = resolve_providers(
        inventory.providers,
        enabled_provider_ids=cfg1.enabled_provider_ids,
        selected_provider_ids={},
    )
    runtime.activate(rep1, factories={p1: _factory}, configs=cfg1.provider_configs)
    lease1 = runtime.lease(c_rsi)
    assert lease1.instance == "instance_gen_1"

    # Switch config to trigger new generation
    cfg2 = ProviderConfiguration(
        enabled_provider_ids=frozenset([p1]),
        provider_configs={p1: {"v": 2}},
    )
    res = reconcile_configuration(
        runtime, inventory, cfg1, cfg2, factories={p1: _factory}
    )
    assert res.rolled_back is False
    lease2 = runtime.lease(c_rsi)
    assert lease2.instance == "instance_gen_2"
    assert lease2.generation_id != lease1.generation_id
