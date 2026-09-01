"""Unit and functional tests for Instrument Catalogue service."""

from __future__ import annotations

from pathlib import Path

import pytest
from app.contracts.catalogue.errors import CatalogueFailure
from app.contracts.catalogue.events import (
    InstrumentVersionCreated,
    InstrumentVersionDeleted,
)
from app.contracts.catalogue.models import (
    CatalogInstrumentsRequest,
    CatalogInstrumentsSuccess,
    InstrumentRef,
    InstrumentVersion,
    OrderConstraints,
)
from app.kernel.events import EventBus
from app.services.catalogue.instrument_catalogue.config import (
    InstrumentCatalogueConfig,
)
from app.services.catalogue.instrument_catalogue.instrument_catalogue import (
    InstrumentCatalogueService,
    fr_cat_define_instruments,
    fr_cat_protect_referenced_versions,
    fr_cat_version_instruments,
    main,
)

_REQ_ID = "00000000-0000-7000-8000-000000000001"
_SNAP_ID = "00000000-0000-7000-8000-000000000002"
_INST_ID_1 = "00000000-0000-7000-8000-000000000010"
_INST_ID_2 = "00000000-0000-7000-8000-000000000011"
_SESSION_ID = "00000000-0000-7000-8000-000000000020"


def _make_instrument(
    instrument_id: str,
    *,
    version: int = 1,
    symbol: str = "EURUSD",
    effective_from: str = "2026-01-01T00:00:00.000000Z",
    content_hash: str = "a" * 64,
    asset_class: str = "FOREX",
    base_currency: str = "EUR",
    quote_currency: str = "USD",
    tick_size: str = "0.00001",
    price_decimals: int = 5,
) -> InstrumentVersion:
    """Helper to build a valid InstrumentVersion wire record."""
    return InstrumentVersion(
        instrument_id=instrument_id,
        version=version,
        symbol=symbol,
        display_name=f"{symbol} Test Instrument",
        asset_class=asset_class,  # type: ignore[arg-type]
        base_currency=base_currency,
        quote_currency=quote_currency,
        settlement_currency=quote_currency,
        point_value="100000",
        tick_size=tick_size,
        price_decimals=price_decimals,
        quantity_multiplier="1",
        order_constraints=OrderConstraints(
            min_quantity="0.01",
            max_quantity="100",
            quantity_step="0.01",
            min_order_distance="0.00005",
            supported_order_types=("MARKET", "LIMIT"),
            supported_time_in_force=("GTC", "IOC"),
        ),
        default_spread="0.00012",
        exchange="IDEALPRO",
        timezone="America/New_York",
        session_id=_SESSION_ID,
        effective_from=effective_from,
        content_hash=content_hash,
    )


@pytest.mark.asyncio
async def test_cat_define_instruments(tmp_path: Path) -> None:
    """Test FR-CAT-DEFINE_INSTRUMENTS: define canonical instrument, query, list and event publication."""
    events_received: list[InstrumentVersionCreated] = []
    event_bus = EventBus()
    event_bus.subscribe(InstrumentVersionCreated, events_received.append)

    db_path = tmp_path / "cat.db"
    service = InstrumentCatalogueService(
        config=InstrumentCatalogueConfig(database_path=db_path),
        event_bus=event_bus,
    )

    inst_v1 = _make_instrument(_INST_ID_1, version=1, symbol="EURUSD")
    upsert_req = CatalogInstrumentsRequest(
        request_id=_REQ_ID,
        capability_snapshot_id=_SNAP_ID,
        operation="UPSERT_VERSION",
        instrument_version=inst_v1,
    )

    result = await fr_cat_define_instruments(service, upsert_req)
    assert isinstance(result, CatalogInstrumentsSuccess)
    assert len(result.instruments) == 1
    assert result.instruments[0].symbol == "EURUSD"
    assert result.instruments[0].version == 1
    assert len(events_received) == 1
    assert events_received[0].instrument.instrument_id == _INST_ID_1

    # Query by GET
    get_req = CatalogInstrumentsRequest(
        request_id=_REQ_ID,
        capability_snapshot_id=_SNAP_ID,
        operation="GET",
        instrument_ref=InstrumentRef(instrument_id=_INST_ID_1),
    )
    get_res = await fr_cat_define_instruments(service, get_req)
    assert isinstance(get_res, CatalogInstrumentsSuccess)
    assert len(get_res.instruments) == 1
    assert get_res.instruments[0].instrument_id == _INST_ID_1

    # Define a second instrument and test LIST with pagination
    inst_v2 = _make_instrument(_INST_ID_2, version=1, symbol="GBPUSD")
    await fr_cat_define_instruments(
        service,
        CatalogInstrumentsRequest(
            request_id=_REQ_ID,
            capability_snapshot_id=_SNAP_ID,
            operation="UPSERT_VERSION",
            instrument_version=inst_v2,
        ),
    )

    list_req = CatalogInstrumentsRequest(
        request_id=_REQ_ID,
        capability_snapshot_id=_SNAP_ID,
        operation="LIST",
        page_size=1,
    )
    list_res = await fr_cat_define_instruments(service, list_req)
    assert isinstance(list_res, CatalogInstrumentsSuccess)
    assert len(list_res.instruments) == 1
    assert list_res.next_cursor is not None

    list_page2 = CatalogInstrumentsRequest(
        request_id=_REQ_ID,
        capability_snapshot_id=_SNAP_ID,
        operation="LIST",
        page_size=1,
        page_cursor=list_res.next_cursor,
    )
    list_res2 = await fr_cat_define_instruments(service, list_page2)
    assert isinstance(list_res2, CatalogInstrumentsSuccess)
    assert len(list_res2.instruments) == 1
    assert (
        list_res2.instruments[0].instrument_id != list_res.instruments[0].instrument_id
    )


@pytest.mark.asyncio
async def test_cat_define_instruments_validation_rejections() -> None:
    """Test model validation rejects invalid tick precision and non-index equal currencies."""
    with pytest.raises(
        ValueError, match="tick_size must be representable at price_decimals"
    ):
        _make_instrument(_INST_ID_1, tick_size="0.000001", price_decimals=5)

    with pytest.raises(
        ValueError,
        match="base and quote currencies may be equal only for a reference INDEX",
    ):
        _make_instrument(
            _INST_ID_1,
            base_currency="USD",
            quote_currency="USD",
            asset_class="FOREX",
        )

    # Equal base and quote is permitted for INDEX
    index_inst = _make_instrument(
        _INST_ID_1,
        asset_class="INDEX",
        base_currency="SPX",
        quote_currency="SPX",
    )
    assert index_inst.base_currency == index_inst.quote_currency


@pytest.mark.asyncio
async def test_cat_version_instruments(tmp_path: Path) -> None:
    """Test FR-CAT-VERSION_INSTRUMENTS: versioning, sequencing, interval closure, and idempotency."""
    service = InstrumentCatalogueService(
        config=InstrumentCatalogueConfig(database_path=tmp_path / "cat.db")
    )

    v1 = _make_instrument(
        _INST_ID_1, version=1, effective_from="2026-01-01T00:00:00.000000Z"
    )
    await fr_cat_define_instruments(
        service,
        CatalogInstrumentsRequest(
            request_id=_REQ_ID,
            capability_snapshot_id=_SNAP_ID,
            operation="UPSERT_VERSION",
            instrument_version=v1,
        ),
    )

    # Idempotent re-put of same version with same content hash
    idempotent_res = await fr_cat_version_instruments(
        service,
        CatalogInstrumentsRequest(
            request_id=_REQ_ID,
            capability_snapshot_id=_SNAP_ID,
            operation="UPSERT_VERSION",
            instrument_version=v1,
        ),
    )
    assert isinstance(idempotent_res, CatalogInstrumentsSuccess)

    # Version sequence jump (trying version 3 instead of 2) -> conflict
    v3_jump = _make_instrument(
        _INST_ID_1, version=3, effective_from="2026-06-01T00:00:00.000000Z"
    )
    conflict_res = await fr_cat_version_instruments(
        service,
        CatalogInstrumentsRequest(
            request_id=_REQ_ID,
            capability_snapshot_id=_SNAP_ID,
            operation="UPSERT_VERSION",
            instrument_version=v3_jump,
        ),
    )
    assert isinstance(conflict_res, CatalogueFailure)
    assert conflict_res.code == "CATALOGUE_VERSION_CONFLICT"

    # Mismatched expected_version
    v2 = _make_instrument(
        _INST_ID_1,
        version=2,
        effective_from="2026-06-01T00:00:00.000000Z",
        content_hash="b" * 64,
    )
    exp_conflict = await fr_cat_version_instruments(
        service,
        CatalogInstrumentsRequest(
            request_id=_REQ_ID,
            capability_snapshot_id=_SNAP_ID,
            operation="UPSERT_VERSION",
            instrument_version=v2,
            expected_version=99,
        ),
    )
    assert isinstance(exp_conflict, CatalogueFailure)
    assert exp_conflict.code == "CATALOGUE_VERSION_CONFLICT"

    # Valid version 2 creation
    v2_res = await fr_cat_version_instruments(
        service,
        CatalogInstrumentsRequest(
            request_id=_REQ_ID,
            capability_snapshot_id=_SNAP_ID,
            operation="UPSERT_VERSION",
            instrument_version=v2,
            expected_version=1,
        ),
    )
    assert isinstance(v2_res, CatalogInstrumentsSuccess)
    assert v2_res.instruments[0].version == 2

    # GET returns latest version (v2)
    get_res = await service.catalog_instruments(
        CatalogInstrumentsRequest(
            request_id=_REQ_ID,
            capability_snapshot_id=_SNAP_ID,
            operation="GET",
            instrument_ref=InstrumentRef(instrument_id=_INST_ID_1),
        )
    )
    assert isinstance(get_res, CatalogInstrumentsSuccess)
    assert get_res.instruments[0].version == 2


@pytest.mark.asyncio
async def test_cat_protect_referenced_versions(tmp_path: Path) -> None:
    """Test FR-CAT-PROTECT_REFERENCED_VERSIONS: deletion protection, failure codes, and clean deletion."""
    events_received: list[InstrumentVersionDeleted] = []
    event_bus = EventBus()
    event_bus.subscribe(InstrumentVersionDeleted, events_received.append)

    service = InstrumentCatalogueService(
        config=InstrumentCatalogueConfig(database_path=tmp_path / "cat.db"),
        event_bus=event_bus,
    )

    v1 = _make_instrument(_INST_ID_1, version=1)
    await service.catalog_instruments(
        CatalogInstrumentsRequest(
            request_id=_REQ_ID,
            capability_snapshot_id=_SNAP_ID,
            operation="UPSERT_VERSION",
            instrument_version=v1,
        )
    )

    # Protect version 1 with a committed manifest reference
    service.record_manifest_reference(
        instrument_id=_INST_ID_1,
        version=1,
        manifest_id="manifest-run-2026-001",
    )
    assert service.is_version_referenced(_INST_ID_1, 1) is True

    # Attempt deletion on protected version -> CATALOGUE_REFERENCE_PROTECTED
    del_protected = await fr_cat_protect_referenced_versions(
        service,
        CatalogInstrumentsRequest(
            request_id=_REQ_ID,
            capability_snapshot_id=_SNAP_ID,
            operation="DELETE_VERSION",
            instrument_ref=InstrumentRef(instrument_id=_INST_ID_1),
            expected_version=1,
        ),
    )
    assert isinstance(del_protected, CatalogueFailure)
    assert del_protected.code == "CATALOGUE_REFERENCE_PROTECTED"
    assert len(events_received) == 0

    # Non-existent instrument deletion -> CATALOGUE_NOT_FOUND
    del_not_found = await service.catalog_instruments(
        CatalogInstrumentsRequest(
            request_id=_REQ_ID,
            capability_snapshot_id=_SNAP_ID,
            operation="DELETE_VERSION",
            instrument_ref=InstrumentRef(instrument_id=_INST_ID_2),
            expected_version=1,
        )
    )
    assert isinstance(del_not_found, CatalogueFailure)
    assert del_not_found.code == "CATALOGUE_NOT_FOUND"

    # Add unreferenced instrument and delete it cleanly
    v_unref = _make_instrument(_INST_ID_2, version=1, symbol="USDJPY")
    await service.catalog_instruments(
        CatalogInstrumentsRequest(
            request_id=_REQ_ID,
            capability_snapshot_id=_SNAP_ID,
            operation="UPSERT_VERSION",
            instrument_version=v_unref,
        )
    )
    del_success = await service.catalog_instruments(
        CatalogInstrumentsRequest(
            request_id=_REQ_ID,
            capability_snapshot_id=_SNAP_ID,
            operation="DELETE_VERSION",
            instrument_ref=InstrumentRef(instrument_id=_INST_ID_2),
            expected_version=1,
        )
    )
    assert isinstance(del_success, CatalogInstrumentsSuccess)
    assert del_success.deleted is True
    assert len(events_received) == 1
    assert events_received[0].instrument.instrument_id == _INST_ID_2


@pytest.mark.asyncio
async def test_executable_usage_main() -> None:
    """Test executable __main__ scenario runner finishes cleanly without exceptions."""
    await main()
