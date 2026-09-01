"""Unit and functional tests for Provider and Broker Mapping service."""

from __future__ import annotations

from pathlib import Path

import pytest
from app.contracts.catalogue.errors import CatalogueFailure
from app.contracts.catalogue.events import (
    ProviderSymbolMappingChanged,
    ProviderSymbolMappingDeleted,
)
from app.contracts.catalogue.models import (
    BrokerRef,
    InstrumentRef,
    MapProvidersRequest,
    MapProvidersSuccess,
    ProviderRef,
    ProviderSymbolMapping,
)
from app.kernel.events import EventBus
from app.services.catalogue.provider_mapping.config import (
    ProviderMappingConfig,
)
from app.services.catalogue.provider_mapping.provider_mapping import (
    ProviderMappingService,
    fr_cat_map_broker_symbols,
    fr_cat_map_provider_identities,
    main,
)

_REQ_ID = "00000000-0000-7000-8000-000000000001"
_SNAP_ID = "00000000-0000-7000-8000-000000000002"
_INST_ID = "00000000-0000-7000-8000-000000000010"
_PROV_ID = "00000000-0000-7000-8000-000000000030"
_BROKER_A_ID = "00000000-0000-7000-8000-000000000040"
_BROKER_B_ID = "00000000-0000-7000-8000-000000000041"
_MAPPING_A_ID = "00000000-0000-7000-8000-000000000050"
_MAPPING_B_ID = "00000000-0000-7000-8000-000000000051"
_MAPPING_C_ID = "00000000-0000-7000-8000-000000000052"


def _make_mapping(
    mapping_id: str,
    *,
    instrument_id: str = _INST_ID,
    instrument_version: int = 1,
    provider_id: str = _PROV_ID,
    provider_name: str = "MetaTrader5",
    broker_id: str | None = None,
    broker_name: str | None = None,
    provider_symbol: str = "EURUSD",
    effective_from: str = "2026-01-01T00:00:00.000000Z",
    effective_to: str | None = None,
    content_hash: str = "a" * 64,
) -> ProviderSymbolMapping:
    """Helper to build a valid ProviderSymbolMapping wire record."""
    broker_ref = (
        BrokerRef(broker_id=broker_id, broker_name=broker_name or "TestBroker")
        if broker_id is not None
        else None
    )
    return ProviderSymbolMapping(
        mapping_id=mapping_id,
        instrument=InstrumentRef(instrument_id=instrument_id),
        instrument_version=instrument_version,
        provider=ProviderRef(provider_id=provider_id, provider_name=provider_name),
        broker=broker_ref,
        provider_symbol=provider_symbol,
        effective_from=effective_from,
        effective_to=effective_to,
        content_hash=content_hash,
    )


@pytest.mark.asyncio
async def test_cat_map_broker_symbols(tmp_path: Path) -> None:
    """Test FR-CAT-MAP_BROKER_SYMBOLS: broker profiles mapping canonical instruments without conflict."""
    events_received: list[ProviderSymbolMappingChanged] = []
    event_bus = EventBus()
    event_bus.subscribe(ProviderSymbolMappingChanged, events_received.append)

    db_path = tmp_path / "mappings.db"
    service = ProviderMappingService(
        config=ProviderMappingConfig(database_path=db_path),
        event_bus=event_bus,
    )

    # Broker A maps EURUSD to EURUSD.raw
    map_a = _make_mapping(
        _MAPPING_A_ID,
        broker_id=_BROKER_A_ID,
        broker_name="BrokerAlpha",
        provider_symbol="EURUSD.raw",
    )
    res_a = await fr_cat_map_broker_symbols(
        service,
        MapProvidersRequest(
            request_id=_REQ_ID,
            capability_snapshot_id=_SNAP_ID,
            operation="UPSERT",
            mapping=map_a,
        ),
    )
    assert isinstance(res_a, MapProvidersSuccess)
    assert len(res_a.mappings) == 1
    assert res_a.mappings[0].provider_symbol == "EURUSD.raw"
    assert len(events_received) == 1

    # Broker B maps same EURUSD to EURUSD_pro without conflict
    map_b = _make_mapping(
        _MAPPING_B_ID,
        broker_id=_BROKER_B_ID,
        broker_name="BrokerBeta",
        provider_symbol="EURUSD_pro",
        content_hash="b" * 64,
    )
    res_b = await fr_cat_map_broker_symbols(
        service,
        MapProvidersRequest(
            request_id=_REQ_ID,
            capability_snapshot_id=_SNAP_ID,
            operation="UPSERT",
            mapping=map_b,
        ),
    )
    assert isinstance(res_b, MapProvidersSuccess)
    assert len(res_b.mappings) == 1
    assert res_b.mappings[0].provider_symbol == "EURUSD_pro"
    assert len(events_received) == 2

    # Resolve with Broker A
    resolve_a = await fr_cat_map_broker_symbols(
        service,
        MapProvidersRequest(
            request_id=_REQ_ID,
            capability_snapshot_id=_SNAP_ID,
            operation="RESOLVE",
            provider=ProviderRef(provider_id=_PROV_ID, provider_name="MetaTrader5"),
            broker=BrokerRef(broker_id=_BROKER_A_ID, broker_name="BrokerAlpha"),
            provider_symbol="EURUSD.raw",
            as_of="2026-06-01T00:00:00.000000Z",
        ),
    )
    assert isinstance(resolve_a, MapProvidersSuccess)
    assert len(resolve_a.mappings) == 1
    assert resolve_a.mappings[0].broker is not None
    assert resolve_a.mappings[0].broker.broker_id == _BROKER_A_ID

    # Resolve with Broker B
    resolve_b = await fr_cat_map_broker_symbols(
        service,
        MapProvidersRequest(
            request_id=_REQ_ID,
            capability_snapshot_id=_SNAP_ID,
            operation="RESOLVE",
            provider=ProviderRef(provider_id=_PROV_ID, provider_name="MetaTrader5"),
            broker=BrokerRef(broker_id=_BROKER_B_ID, broker_name="BrokerBeta"),
            provider_symbol="EURUSD_pro",
            as_of="2026-06-01T00:00:00.000000Z",
        ),
    )
    assert isinstance(resolve_b, MapProvidersSuccess)
    assert len(resolve_b.mappings) == 1
    assert resolve_b.mappings[0].broker is not None
    assert resolve_b.mappings[0].broker.broker_id == _BROKER_B_ID


@pytest.mark.asyncio
async def test_cat_map_provider_identities(tmp_path: Path) -> None:
    """Test FR-CAT-MAP_PROVIDER_IDENTITIES: versioned adapter mapping and point-in-time resolution."""
    service = ProviderMappingService(
        config=ProviderMappingConfig(database_path=tmp_path / "mappings.db"),
    )

    # Historical mapping valid 2026-01-01 to 2026-07-01
    map_h1 = _make_mapping(
        _MAPPING_A_ID,
        provider_symbol="EUR_USD",
        effective_from="2026-01-01T00:00:00.000000Z",
        effective_to="2026-07-01T00:00:00.000000Z",
        content_hash="1" * 64,
    )
    await fr_cat_map_provider_identities(
        service,
        MapProvidersRequest(
            request_id=_REQ_ID,
            capability_snapshot_id=_SNAP_ID,
            operation="UPSERT",
            mapping=map_h1,
        ),
    )

    # Subsequent mapping valid from 2026-07-01 onward
    map_h2 = _make_mapping(
        _MAPPING_B_ID,
        provider_symbol="EUR_USD",
        effective_from="2026-07-01T00:00:00.000000Z",
        effective_to=None,
        content_hash="2" * 64,
    )
    await fr_cat_map_provider_identities(
        service,
        MapProvidersRequest(
            request_id=_REQ_ID,
            capability_snapshot_id=_SNAP_ID,
            operation="UPSERT",
            mapping=map_h2,
        ),
    )

    prov_ref = ProviderRef(provider_id=_PROV_ID, provider_name="MetaTrader5")

    # Point-in-time query in H1
    res_h1 = await fr_cat_map_provider_identities(
        service,
        MapProvidersRequest(
            request_id=_REQ_ID,
            capability_snapshot_id=_SNAP_ID,
            operation="RESOLVE",
            provider=prov_ref,
            provider_symbol="EUR_USD",
            as_of="2026-03-01T00:00:00.000000Z",
        ),
    )
    assert isinstance(res_h1, MapProvidersSuccess)
    assert res_h1.mappings[0].mapping_id == _MAPPING_A_ID
    assert res_h1.mappings[0].provider_symbol == "EUR_USD"

    # Point-in-time query in H2
    res_h2 = await fr_cat_map_provider_identities(
        service,
        MapProvidersRequest(
            request_id=_REQ_ID,
            capability_snapshot_id=_SNAP_ID,
            operation="RESOLVE",
            provider=prov_ref,
            provider_symbol="EUR_USD",
            as_of="2026-08-01T00:00:00.000000Z",
        ),
    )
    assert isinstance(res_h2, MapProvidersSuccess)
    assert res_h2.mappings[0].mapping_id == _MAPPING_B_ID
    assert res_h2.mappings[0].provider_symbol == "EUR_USD"

    # Query before start of intervals returns not found
    res_before = await fr_cat_map_provider_identities(
        service,
        MapProvidersRequest(
            request_id=_REQ_ID,
            capability_snapshot_id=_SNAP_ID,
            operation="RESOLVE",
            provider=prov_ref,
            provider_symbol="EUR_USD",
            as_of="2025-12-31T00:00:00.000000Z",
        ),
    )
    assert isinstance(res_before, CatalogueFailure)
    assert res_before.code == "CATALOGUE_NOT_FOUND"


@pytest.mark.asyncio
async def test_mapping_overlap_rejection(tmp_path: Path) -> None:
    """Test rejection of overlapping intervals with CATALOGUE_MAPPING_OVERLAP."""
    service = ProviderMappingService(
        config=ProviderMappingConfig(database_path=tmp_path / "mappings.db"),
    )

    map_1 = _make_mapping(
        _MAPPING_A_ID,
        provider_symbol="EURUSD",
        effective_from="2026-01-01T00:00:00.000000Z",
        effective_to="2026-06-01T00:00:00.000000Z",
        content_hash="1" * 64,
    )
    res_1 = await service.map_providers(
        MapProvidersRequest(
            request_id=_REQ_ID,
            capability_snapshot_id=_SNAP_ID,
            operation="UPSERT",
            mapping=map_1,
        )
    )
    assert isinstance(res_1, MapProvidersSuccess)

    # Overlapping mapping (2026-03-01 to 2026-09-01) for same provider and symbol
    map_overlap = _make_mapping(
        _MAPPING_B_ID,
        provider_symbol="EURUSD",
        effective_from="2026-03-01T00:00:00.000000Z",
        effective_to="2026-09-01T00:00:00.000000Z",
        content_hash="2" * 64,
    )
    res_overlap = await service.map_providers(
        MapProvidersRequest(
            request_id=_REQ_ID,
            capability_snapshot_id=_SNAP_ID,
            operation="UPSERT",
            mapping=map_overlap,
        )
    )
    assert isinstance(res_overlap, CatalogueFailure)
    assert res_overlap.code == "CATALOGUE_MAPPING_OVERLAP"


@pytest.mark.asyncio
async def test_mapping_idempotency_and_delete(tmp_path: Path) -> None:
    """Test idempotent re-upsert and deletion lifecycle."""
    events_deleted: list[ProviderSymbolMappingDeleted] = []
    event_bus = EventBus()
    event_bus.subscribe(ProviderSymbolMappingDeleted, events_deleted.append)

    service = ProviderMappingService(
        config=ProviderMappingConfig(database_path=tmp_path / "mappings.db"),
        event_bus=event_bus,
    )

    map_1 = _make_mapping(_MAPPING_A_ID)
    upsert_req = MapProvidersRequest(
        request_id=_REQ_ID,
        capability_snapshot_id=_SNAP_ID,
        operation="UPSERT",
        mapping=map_1,
    )
    res_1 = await service.map_providers(upsert_req)
    assert isinstance(res_1, MapProvidersSuccess)

    # Re-upsert identical mapping with same content_hash
    res_reput = await service.map_providers(upsert_req)
    assert isinstance(res_reput, MapProvidersSuccess)

    # Delete mapping
    delete_req = MapProvidersRequest(
        request_id=_REQ_ID,
        capability_snapshot_id=_SNAP_ID,
        operation="DELETE",
        mapping=map_1,
    )
    res_del = await service.map_providers(delete_req)
    assert isinstance(res_del, MapProvidersSuccess)
    assert res_del.deleted is True
    assert len(events_deleted) == 1
    assert events_deleted[0].mapping_id == _MAPPING_A_ID

    # Resolving deleted mapping returns CATALOGUE_NOT_FOUND
    res_query_del = await service.map_providers(
        MapProvidersRequest(
            request_id=_REQ_ID,
            capability_snapshot_id=_SNAP_ID,
            operation="RESOLVE",
            provider=ProviderRef(provider_id=_PROV_ID, provider_name="MetaTrader5"),
            provider_symbol="EURUSD",
            as_of="2026-06-01T00:00:00.000000Z",
        )
    )
    assert isinstance(res_query_del, CatalogueFailure)
    assert res_query_del.code == "CATALOGUE_NOT_FOUND"

    # Deleting already deleted or nonexistent mapping returns CATALOGUE_NOT_FOUND
    res_del_again = await service.map_providers(delete_req)
    assert isinstance(res_del_again, CatalogueFailure)
    assert res_del_again.code == "CATALOGUE_NOT_FOUND"


@pytest.mark.asyncio
async def test_executable_usage_main() -> None:
    """Test executable __main__ scenario runner finishes cleanly without exceptions."""
    await main()
