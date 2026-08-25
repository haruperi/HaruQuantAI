"""Typed Catalogue domain event payloads for the DomainEvent envelope."""

from typing import Literal

from pydantic import Field

# These payload types are annotation-only for readers but Pydantic resolves
# them at class-creation time, so they must remain runtime imports.
from app.contracts.catalogue.models import (  # noqa: TC001
    BrokerRef,
    InstrumentRef,
    NonEmptyStr,
    ProviderRef,
    UniverseRef,
)
from app.contracts.common.models import ContentHash, Uuid7, WireModel


class InstrumentVersionCreated(WireModel):
    """Payload for catalogue.instrument-version-created events."""

    instrument: InstrumentRef
    instrument_version: int = Field(ge=1)
    content_hash: ContentHash
    schema_version: Literal[1] = 1


class InstrumentVersionDeleted(WireModel):
    """Payload for catalogue.instrument-version-deleted events."""

    instrument: InstrumentRef
    instrument_version: int = Field(ge=1)
    prior_content_hash: ContentHash
    schema_version: Literal[1] = 1


class ProviderSymbolMappingChanged(WireModel):
    """Payload for catalogue.provider-symbol-mapping-changed events."""

    mapping_id: Uuid7
    instrument: InstrumentRef
    instrument_version: int = Field(ge=1)
    provider: ProviderRef
    broker: BrokerRef | None
    provider_symbol: NonEmptyStr
    content_hash: ContentHash
    schema_version: Literal[1] = 1


class ProviderSymbolMappingDeleted(WireModel):
    """Payload for catalogue.provider-symbol-mapping-deleted events."""

    mapping_id: Uuid7
    instrument: InstrumentRef
    instrument_version: int = Field(ge=1)
    provider: ProviderRef
    broker: BrokerRef | None
    provider_symbol: NonEmptyStr
    prior_content_hash: ContentHash
    schema_version: Literal[1] = 1


class TradingSessionChanged(WireModel):
    """Payload for catalogue.trading-session-changed events."""

    session_id: Uuid7
    version: int = Field(ge=1)
    content_hash: ContentHash
    schema_version: Literal[1] = 1


class MarketCalendarChanged(WireModel):
    """Payload for catalogue.market-calendar-changed events."""

    calendar_id: Uuid7
    version: int = Field(ge=1)
    content_hash: ContentHash
    schema_version: Literal[1] = 1


class TradingRuleSetChanged(WireModel):
    """Payload for catalogue.trading-rule-set-changed events."""

    rule_set_id: Uuid7
    instrument: InstrumentRef
    instrument_version: int = Field(ge=1)
    content_hash: ContentHash
    schema_version: Literal[1] = 1


class UniverseVersionCreated(WireModel):
    """Payload for catalogue.universe-version-created events."""

    universe: UniverseRef
    version: int = Field(ge=1)
    content_hash: ContentHash
    schema_version: Literal[1] = 1


class CataloguePackageImported(WireModel):
    """Payload for catalogue.package-imported events."""

    package_id: Uuid7
    content_hash: ContentHash
    imported_refs: tuple[Uuid7, ...]
    schema_version: Literal[1] = 1


# Closed event-type discriminator union for the nine catalogue events.
type CatalogueEventType = Literal[
    "catalogue.instrument-version-created",
    "catalogue.instrument-version-deleted",
    "catalogue.provider-symbol-mapping-changed",
    "catalogue.provider-symbol-mapping-deleted",
    "catalogue.trading-session-changed",
    "catalogue.market-calendar-changed",
    "catalogue.trading-rule-set-changed",
    "catalogue.universe-version-created",
    "catalogue.package-imported",
]

WIRE_EVENTS: dict[str, type[WireModel]] = {
    "InstrumentVersionCreated": InstrumentVersionCreated,
    "InstrumentVersionDeleted": InstrumentVersionDeleted,
    "ProviderSymbolMappingChanged": ProviderSymbolMappingChanged,
    "ProviderSymbolMappingDeleted": ProviderSymbolMappingDeleted,
    "TradingSessionChanged": TradingSessionChanged,
    "MarketCalendarChanged": MarketCalendarChanged,
    "TradingRuleSetChanged": TradingRuleSetChanged,
    "UniverseVersionCreated": UniverseVersionCreated,
    "CataloguePackageImported": CataloguePackageImported,
}
