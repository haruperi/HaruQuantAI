"""Catalogue domain capability keys."""

from typing import TYPE_CHECKING

from app.kernel.capability import CapabilityKey

if TYPE_CHECKING:
    from app.contracts.catalogue.ports import (
        CatalogInstrumentsCapability,
        ConvertCurrenciesCapability,
        DefineSessionsCapability,
        DefineTradingRulesCapability,
        ExchangeCatalogueCapability,
        ManageUniversesCapability,
        MapProvidersCapability,
    )

CATALOG_INSTRUMENTS_CAPABILITY: CapabilityKey[CatalogInstrumentsCapability] = (
    CapabilityKey(
        name="catalogue.catalog-instruments",
        major=1,
    )
)

MAP_PROVIDERS_CAPABILITY: CapabilityKey[MapProvidersCapability] = CapabilityKey(
    name="catalogue.map-providers",
    major=1,
)

DEFINE_SESSIONS_CAPABILITY: CapabilityKey[DefineSessionsCapability] = CapabilityKey(
    name="catalogue.define-sessions",
    major=1,
)

DEFINE_TRADING_RULES_CAPABILITY: CapabilityKey[DefineTradingRulesCapability] = (
    CapabilityKey(
        name="catalogue.define-trading-rules",
        major=1,
    )
)

MANAGE_UNIVERSES_CAPABILITY: CapabilityKey[ManageUniversesCapability] = CapabilityKey(
    name="catalogue.manage-universes",
    major=1,
)

CONVERT_CURRENCIES_CAPABILITY: CapabilityKey[ConvertCurrenciesCapability] = (
    CapabilityKey(
        name="catalogue.convert-currencies",
        major=1,
    )
)

EXCHANGE_CATALOGUE_CAPABILITY: CapabilityKey[ExchangeCatalogueCapability] = (
    CapabilityKey(
        name="catalogue.exchange-catalogue",
        major=1,
    )
)
