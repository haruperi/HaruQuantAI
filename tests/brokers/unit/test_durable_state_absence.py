"""Unit evidence verifying that Brokers owns no durable state or migrations."""

from __future__ import annotations

from pathlib import Path

from app.services import brokers
from app.services.brokers.binance.manifest import SPEC as BINANCE_SPEC
from app.services.brokers.ctrader.manifest import SPEC as CTRADER_SPEC
from app.services.brokers.dukascopy.manifest import SPEC as DUKASCOPY_SPEC
from app.services.brokers.metatrader.manifest import SPEC as METATRADER_SPEC
from app.services.brokers.provider_gateway.manifest import SPEC as GATEWAY_SPEC
from app.services.brokers.yahoo.manifest import SPEC as YAHOO_SPEC


def test_brokers_persistence_and_migration_packages_are_absent() -> None:
    """Verify physical absence of persistence and migration support packages."""
    brokers_root = Path("app/services/brokers")
    assert not (brokers_root / "persistence").exists()
    assert not (brokers_root / "migrations").exists()
    assert not (brokers_root / "_shared").exists()
    assert not (brokers_root / "canonical_contracts").exists()
    assert not (brokers_root / "binance" / "health.py").exists()
    assert not (brokers_root / "ctrader" / "health.py").exists()
    assert not (brokers_root / "dukascopy" / "health.py").exists()
    assert not (brokers_root / "metatrader" / "health.py").exists()


def test_brokers_root_exports_no_durable_state_or_migration_symbols() -> None:
    """Verify package root does not expose retired migration or persistence APIs."""
    retired_symbols = (
        "run_broker_migrations",
        "create_health_record",
        "record_binance_health_checkpoint",
        "record_ctrader_health_checkpoint",
        "record_dukascopy_health_checkpoint",
        "record_metatrader_health_checkpoint",
        "record_yahoo_health_checkpoint",
        "persistence",
        "migrations",
    )
    for symbol in retired_symbols:
        assert symbol not in brokers.__all__
        assert not hasattr(brokers, symbol)


def test_all_surviving_broker_manifests_declare_stateless() -> None:
    """Verify all surviving Broker feature manifests specify state=None."""
    surviving_specs = (
        GATEWAY_SPEC,
        YAHOO_SPEC,
        DUKASCOPY_SPEC,
        BINANCE_SPEC,
        CTRADER_SPEC,
        METATRADER_SPEC,
    )
    for spec in surviving_specs:
        assert spec.state is None
        assert spec.domain == "brokers"
