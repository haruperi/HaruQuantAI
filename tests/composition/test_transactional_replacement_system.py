"""End-to-end system test proving transactional provider configuration replacement and rollback.

Traces to: P17-T02, Phase 17, Gate G17
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from app.composition import (
    CompositionRuntime,
    ProviderConfiguration,
    reconcile_configuration,
    replace_provider_configuration,
)
from app.kernel.discovery import discover_manifests
from app.kernel.identifiers import CapabilityId, ProviderId
from app.kernel.registry import build_inventory
from app.kernel.resolver import resolve_providers

if TYPE_CHECKING:
    from collections.abc import Mapping

    from app.kernel.effects import EffectScope

_MANIFEST_PRODUCER_1 = """
[provider]
id = "producer.data.p1"
version = "1.0.0"
entry_point = "mod:factory"

[[provides]]
capability_id = "data.feed.v1"
contract_version = "1.0.0"
cardinality = "many"

[runtime]
profiles = ["research", "live"]
scopes = ["process"]
effect_classes = ["reversible_ephemeral"]
lifecycle = "pure"
reload = "config_restart"
"""

_MANIFEST_PRODUCER_2 = """
[provider]
id = "producer.data.p2"
version = "2.0.0"
entry_point = "mod:factory"

[[provides]]
capability_id = "data.feed.v1"
contract_version = "1.0.0"
cardinality = "many"

[runtime]
profiles = ["research", "live"]
scopes = ["process"]
effect_classes = ["reversible_ephemeral"]
lifecycle = "pure"
reload = "config_restart"
"""

_MANIFEST_CONSUMER = """
[provider]
id = "consumer.analytics.p1"
version = "1.0.0"
entry_point = "mod:factory"

[[provides]]
capability_id = "analytics.result.v1"
contract_version = "1.0.0"
cardinality = "exactly_one"

[[requires]]
capability_id = "data.feed.v1"
cardinality = "exactly_one"
supported_majors = [1]

[runtime]
profiles = ["research", "live"]
scopes = ["process"]
effect_classes = ["reversible_ephemeral"]
lifecycle = "pure"
reload = "config_restart"
"""


def _setup_system(
    tmp_path: Path,
) -> tuple[CompositionRuntime, Any, ProviderConfiguration, dict[ProviderId, Any]]:
    (tmp_path / "prod1").mkdir(parents=True)
    (tmp_path / "prod1" / "manifest.toml").write_text(
        _MANIFEST_PRODUCER_1.strip(), encoding="utf-8"
    )

    (tmp_path / "prod2").mkdir(parents=True)
    (tmp_path / "prod2" / "manifest.toml").write_text(
        _MANIFEST_PRODUCER_2.strip(), encoding="utf-8"
    )

    (tmp_path / "cons").mkdir(parents=True)
    (tmp_path / "cons" / "manifest.toml").write_text(
        _MANIFEST_CONSUMER.strip(), encoding="utf-8"
    )

    discovered = discover_manifests(tmp_path)
    inventory = build_inventory(discovered)

    p_p1 = ProviderId.parse("producer.data.p1")
    p_cons = ProviderId.parse("consumer.analytics.p1")
    feed_cap = CapabilityId.parse("data.feed.v1")

    incumbent_cfg = ProviderConfiguration(
        enabled_provider_ids=frozenset([p_p1, p_cons]),
        selected_provider_ids={feed_cap: p_p1},
        provider_configs={},
    )

    runtime = CompositionRuntime()
    factories: dict[ProviderId, Any] = {
        p_p1: lambda *, dependencies, config, scope: "feed_instance_1",
        p_cons: lambda *, dependencies, config, scope: (
            f"consumer_with_{dependencies[feed_cap]}"
        ),
    }

    rep = resolve_providers(
        inventory.providers,
        enabled_provider_ids=incumbent_cfg.enabled_provider_ids,
        selected_provider_ids=incumbent_cfg.selected_provider_ids,
    )
    runtime.activate(rep, factories=factories, configs={})

    return runtime, inventory, incumbent_cfg, factories


def test_failed_candidate_restores_exact_incumbent(tmp_path: Path) -> None:
    """Verify failing candidate rolls back and restores exact incumbent instances and graph."""
    runtime, inventory, incumbent_cfg, factories = _setup_system(tmp_path)
    p_p2 = ProviderId.parse("producer.data.p2")
    feed_cap = CapabilityId.parse("data.feed.v1")

    incumbent_lease = runtime.lease(feed_cap)
    assert incumbent_lease.instance == "feed_instance_1"

    # Candidate attempts to switch to p2, but factory fails
    candidate_cfg = ProviderConfiguration(
        enabled_provider_ids=frozenset(
            [p_p2, ProviderId.parse("consumer.analytics.p1")]
        ),
        selected_provider_ids={feed_cap: p_p2},
        provider_configs={},
    )

    def _failing_p2(
        *,
        dependencies: Mapping[CapabilityId, object],
        config: Mapping[str, object],
        scope: EffectScope,
    ) -> object:
        _ = (dependencies, config, scope)
        raise RuntimeError("Candidate readiness failed")

    factories[p_p2] = _failing_p2

    res = reconcile_configuration(
        runtime,
        inventory,
        incumbent_cfg,
        candidate_cfg,
        factories=factories,
    )
    assert res.rolled_back is True

    # After rollback, exact incumbent lease remains valid and active
    restored_lease = runtime.lease(feed_cap)
    assert restored_lease.instance == "feed_instance_1"


def test_inflight_lease_survives_successful_switch(tmp_path: Path) -> None:
    """Verify existing leases continue referencing old generation after successful switch."""
    runtime, inventory, incumbent_cfg, factories = _setup_system(tmp_path)
    p_p2 = ProviderId.parse("producer.data.p2")
    feed_cap = CapabilityId.parse("data.feed.v1")

    old_lease = runtime.lease(feed_cap)
    assert old_lease.instance == "feed_instance_1"

    candidate_cfg = ProviderConfiguration(
        enabled_provider_ids=frozenset(
            [p_p2, ProviderId.parse("consumer.analytics.p1")]
        ),
        selected_provider_ids={feed_cap: p_p2},
        provider_configs={},
    )
    factories[p_p2] = lambda *, dependencies, config, scope: "feed_instance_2"

    evidence = replace_provider_configuration(
        runtime,
        inventory,
        incumbent_cfg,
        candidate_cfg,
        factories=factories,
        request_id="req-switch",
    )

    assert not evidence.rolled_back
    assert "producer.data.p2" in evidence.changed_provider_ids

    # Old lease instance is unchanged
    assert old_lease.instance == "feed_instance_1"

    # New lease yields updated generation
    new_lease = runtime.lease(feed_cap)
    assert new_lease.instance == "feed_instance_2"
    assert new_lease.generation_id != old_lease.generation_id


def test_successful_switch_drains_old_generation(tmp_path: Path) -> None:
    """Verify pin_graph returns only active generations following successful switch."""
    runtime, inventory, incumbent_cfg, factories = _setup_system(tmp_path)
    p_p2 = ProviderId.parse("producer.data.p2")
    feed_cap = CapabilityId.parse("data.feed.v1")

    candidate_cfg = ProviderConfiguration(
        enabled_provider_ids=frozenset(
            [p_p2, ProviderId.parse("consumer.analytics.p1")]
        ),
        selected_provider_ids={feed_cap: p_p2},
        provider_configs={},
    )
    factories[p_p2] = lambda *, dependencies, config, scope: "feed_instance_2"

    replace_provider_configuration(
        runtime,
        inventory,
        incumbent_cfg,
        candidate_cfg,
        factories=factories,
        request_id="req-drain",
    )

    pinned = runtime.pin_graph()
    active_pids = set(pinned.generations.keys())
    assert p_p2 in active_pids
    assert ProviderId.parse("producer.data.p1") not in active_pids


def test_candidate_cleanup_has_zero_resources(tmp_path: Path) -> None:
    """Verify deactivating runtime cleans up all active component state."""
    runtime, _, _, _ = _setup_system(tmp_path)
    runtime.deactivate_all()
    pinned = runtime.pin_graph()
    assert len(pinned.generations) == 0
    assert len(pinned.leases) == 0
