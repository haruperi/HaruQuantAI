"""Manifest ownership tests for the focused Broker architecture."""

from app.contracts.broker.capabilities import (
    MANAGE_SESSIONS_CAPABILITY,
    READ_PROVIDER_STATE_CAPABILITY,
    TRANSPORT_ORDERS_CAPABILITY,
)
from app.services.brokers.binance.manifest import SPEC as BINANCE_SPEC
from app.services.brokers.ctrader.manifest import SPEC as CTRADER_SPEC
from app.services.brokers.dispatch_providers.manifest import SPEC as DISPATCH_SPEC
from app.services.brokers.dukascopy.manifest import SPEC as DUKASCOPY_SPEC
from app.services.brokers.metatrader.manifest import SPEC as MT5_SPEC
from app.services.brokers.yahoo.manifest import SPEC as YAHOO_SPEC


def test_only_dispatcher_provides_public_broker_capabilities() -> None:
    public = {
        MANAGE_SESSIONS_CAPABILITY,
        READ_PROVIDER_STATE_CAPABILITY,
        TRANSPORT_ORDERS_CAPABILITY,
    }
    assert DISPATCH_SPEC.provides == frozenset(public)
    for spec in (
        MT5_SPEC,
        CTRADER_SPEC,
        BINANCE_SPEC,
        DUKASCOPY_SPEC,
        YAHOO_SPEC,
    ):
        assert not (spec.provides & public)


def test_provider_features_have_no_hard_cross_feature_dependencies() -> None:
    for spec in (
        MT5_SPEC,
        CTRADER_SPEC,
        BINANCE_SPEC,
        DUKASCOPY_SPEC,
        YAHOO_SPEC,
    ):
        assert spec.requires == frozenset()
