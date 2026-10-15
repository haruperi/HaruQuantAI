"""Unit tests for Stage 2C market data provider discovery and SC-02 invariant enforcement.

Covers:
- Dynamic discovery of all 9 market data provider plugins under slot `data.provider`.
- Manifest schema validation (id, slot, version, entry_point, capabilities).
- SC-02 Invariant: Aliases normalize to canonical keys; disabled providers cannot be resurrected.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from app.host.discovery import (
    PluginDiscoveryEngine,
    PluginLifecycleManager,
    SlotDefinition,
    SlotRegistry,
)
from app.services.brokers.capabilities import ProviderDisabledError
from app.services.brokers.registry import (
    CANONICAL_PROVIDERS,
    BrokerKey,
    BrokerRegistry,
    normalize_broker_name,
    normalize_provider_id,
)


def test_normalize_provider_id_and_aliases() -> None:
    """Verify alias normalization across all supported broker aliases."""
    expected_mappings = {
        "binance": "crypto",
        "crypto": "crypto",
        "darwinex": "darwinex",
        "dukascopy": "dukascopy",
        "equity": "sq_equity",
        "sq_equity": "sq_equity",
        "file": "files",
        "files": "files",
        "futures": "sq_futures",
        "sq_futures": "sq_futures",
        "metatrader": "metatrader",
        "mt4": "metatrader",
        "mt5": "metatrader",
        "tick_downloader": "tick_downloader",
        "yahoo": "yahoo",
        "data_provider_dukascopy": "dukascopy",
        "datasource_yahoo": "yahoo",
    }
    for alias, canonical in expected_mappings.items():
        assert normalize_provider_id(alias) == canonical
        assert normalize_broker_name(alias) == canonical
        assert BrokerKey.from_str(alias).canonical_id() == canonical


def test_discovery_engine_discovers_all_nine_providers(tmp_path: Path) -> None:
    """Verify PluginDiscoveryEngine discovers all 9 built-in provider plugins."""
    slot_reg = SlotRegistry()
    slot_reg.register_slot(
        SlotDefinition(
            slot_id="data.provider",
            description="Market Data Provider",
            allow_multiple=True,
        )
    )

    brokers_dir = Path(__file__).resolve().parents[4] / "app" / "services" / "brokers"
    engine = PluginDiscoveryEngine(search_dirs=[brokers_dir], slot_registry=slot_reg)
    records = engine.discover()

    for pid in CANONICAL_PROVIDERS:
        assert pid in records, (
            f"Expected {pid} to be discovered by PluginDiscoveryEngine"
        )
        rec = records[pid]
        assert rec.manifest.slot == "data.provider"
        assert rec.manifest.version == "1.0.0"
        assert rec.manifest.entry_point.endswith(":create_adapter")
        assert "data.fetch" in rec.manifest.capabilities


def test_lifecycle_manager_attaches_and_calls_factory_hook(tmp_path: Path) -> None:
    """Verify PluginLifecycleManager attaches all 9 plugins and invokes hook."""
    slot_reg = SlotRegistry()
    slot_reg.register_slot(
        SlotDefinition(
            slot_id="data.provider",
            description="Market Data Provider",
            allow_multiple=True,
        )
    )

    brokers_dir = Path(__file__).resolve().parents[4] / "app" / "services" / "brokers"
    engine = PluginDiscoveryEngine(search_dirs=[brokers_dir], slot_registry=slot_reg)
    engine.discover()

    attached_plugins: list[str] = []

    def hook(plugin_id: str, record: object, context: object) -> object:
        attached_plugins.append(plugin_id)
        return None

    lifecycle = PluginLifecycleManager(
        discovery_engine=engine,
        data_root=tmp_path / "plugins_data",
        instance_factory_hook=hook,
    )
    report = lifecycle.load_and_attach_all()
    assert report.total_discovered >= 9
    assert report.enabled_count >= 9

    for pid in CANONICAL_PROVIDERS:
        assert pid in attached_plugins


def test_sc02_disablement_and_alias_resurrection_protection() -> None:
    """Verify SC-02 invariant: disabling a provider blocks all alias lookups."""
    registry = BrokerRegistry()

    # Verify initial enabled state
    assert registry.is_enabled("crypto") is True
    assert registry.is_enabled("binance") is True

    # Disable by canonical ID
    registry.disable("crypto")
    assert registry.is_enabled("crypto") is False
    assert registry.is_enabled("binance") is False

    # Attempting to acquire via canonical ID or alias must raise ProviderDisabledError
    with pytest.raises(ProviderDisabledError) as exc_canon:
        registry.acquire("crypto")
    assert exc_canon.value.provider == "crypto"

    with pytest.raises(ProviderDisabledError) as exc_alias:
        registry.acquire("binance")
    assert exc_alias.value.provider == "crypto"

    # Attempting to query via HistoricalProviderView
    views = registry.list_historical_providers()
    assert not any(v.name == "crypto" for v in views)

    # Health check returns DISABLED
    health = registry.check_provider_health("crypto")
    assert health.status == "DISABLED"
    assert health.connected is False

    health_alias = registry.check_provider_health("binance")
    assert health_alias.status == "DISABLED"

    # Re-enabling restores access
    registry.enable("crypto")
    assert registry.is_enabled("crypto") is True
    assert registry.is_enabled("binance") is True
    instance = registry.acquire("binance")
    assert instance is not None
    registry.release("binance")
    registry.close()


def test_sc02_disablement_via_alias() -> None:
    """Verify that disabling a provider via an alias disables the canonical key."""
    registry = BrokerRegistry()
    registry.disable("mt5")
    assert registry.is_enabled("metatrader") is False
    assert registry.is_enabled("mt4") is False
    assert registry.is_enabled("mt5") is False

    with pytest.raises(ProviderDisabledError):
        registry.acquire("metatrader")

    with pytest.raises(ProviderDisabledError):
        registry.acquire("mt5")

    registry.enable("metatrader")
    assert registry.is_enabled("metatrader") is True
    registry.close()
