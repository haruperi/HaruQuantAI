"""Unit tests for the browse-reference service and feature."""

from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid7

import pytest
from app.contracts.data.errors import DataFailure
from app.contracts.data.models import (
    BrowseReferenceRequest,
    BrowseReferenceSuccess,
)
from app.kernel.context import DefaultFeatureContext
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope
from app.services.data.browse_reference.browse_reference import (
    BrowseReferenceService,
)
from app.services.data.browse_reference.config import (
    BrowseReferenceConfig,
    from_dict,
)
from app.services.data.browse_reference.feature import BrowseReferenceFeature
from app.services.data.browse_reference.manifest import SPEC


def _request(operation: str, **kwargs: object) -> BrowseReferenceRequest:
    """Build one operation request."""
    return BrowseReferenceRequest(
        request_id=str(uuid7()),
        operation=operation,  # type: ignore[arg-type]
        **kwargs,  # type: ignore[arg-type]
    )


def test_manifest_spec() -> None:
    """Verify feature specification and declared durable state."""
    assert SPEC.feature_id == "FEAT-DATA-BROWSE_REFERENCE"
    (provided,) = SPEC.provides
    assert provided.identifier == "data.browse-reference@1"
    assert SPEC.state is not None
    assert SPEC.state.namespace == "data.browse_reference"
    SPEC.validate()


def test_config_validation(tmp_path: Path) -> None:
    """Verify config rejects unknown keys and accepts valid database path."""
    valid_db = tmp_path / "test.db"
    cfg = BrowseReferenceConfig(database_path=valid_db)
    assert Path(cfg.database_path) == valid_db

    parsed = from_dict({"database_path": str(valid_db)})
    assert Path(parsed.database_path) == valid_db

    with pytest.raises(ValueError, match="Unknown browse-reference configuration keys"):
        from_dict({"unknown_key": "val"})


@pytest.mark.asyncio
async def test_feature_mount_and_service(tmp_path: Path) -> None:
    """Verify feature mounts cleanly into context and registers cleanup."""
    db_file = tmp_path / "ref.db"
    feat = BrowseReferenceFeature()
    assert feat.service is None

    registry = ServiceRegistry()
    scope = FeatureScope(owner_id="FEAT-DATA-BROWSE_REFERENCE")
    context = DefaultFeatureContext(
        spec=feat.spec,
        scope=scope,
        resolver=registry.resolve,
        provider_registrar=lambda cap, impl, sc: registry.register(
            cap, impl, owner_id=sc.owner_id, scope=sc
        ),
    )

    await feat.mount(context, {"database_path": str(db_file)})
    assert feat.service is not None

    await scope.close()
    assert feat.service.closed is True


def _seed_test_db(service: BrowseReferenceService) -> None:
    """Insert initial test records into service database."""
    with service._conn:
        service._conn.execute(
            """
            INSERT INTO broker (id, name, desc, timezone)
            VALUES (1, 'MetaTrader 5', 'MT5 profile', 'UTC')
            """
        )
        service._conn.execute(
            """
            INSERT INTO instruments (
                name, description, path, category, point,
                trade_contract_size, trade_tick_size, spread, volume_min, volume_step
            ) VALUES (
                'EURUSD', 'Euro vs US Dollar', 'Forex/Majors', 'Forex', 0.00001,
                100000.0, 0.00001, 1.2, 0.01, 0.01
            )
            """
        )
        service._conn.execute(
            """
            INSERT INTO data (
                id, symbol, instrument, filename, timeframe, timezone,
                date_from, date_to, row_count, decimals, source,
                created_at, updated_at
            ) VALUES (
                1, 'EURUSD', 'EURUSD', 'EURUSD_H1.csv', 'H1', 'UTC',
                1000, 87400, 50, 5, 1, '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z'
            )
            """
        )
        bars = [
            {
                "time": "2026-08-01T00:00:00Z",
                "open": 1.1,
                "high": 1.2,
                "low": 1.0,
                "close": 1.15,
                "volume": 100,
            },
            {
                "time": "2026-08-01T01:00:00Z",
                "open": 1.15,
                "high": 1.25,
                "low": 1.1,
                "close": 1.2,
                "volume": 120,
            },
        ]
        service._conn.execute(
            """
            INSERT INTO data_bars (symbol, timeframe, records_json, start, end, updated_at)
            VALUES ('EURUSD', 'H1', ?, '2026-08-01T00:00:00Z', '2026-08-01T01:00:00Z', '2026-08-01T01:00:00Z')
            """,
            (json.dumps(bars),),
        )


@pytest.mark.asyncio
async def test_browse_reference_service_reads(tmp_path: Path) -> None:
    """Verify read operations against populated SQLite."""
    db_file = tmp_path / "test_reads.db"
    service = BrowseReferenceService(BrowseReferenceConfig(database_path=str(db_file)))
    _seed_test_db(service)

    res = await service.browse_reference(_request("LIST_CAPABILITIES"))
    assert isinstance(res, BrowseReferenceSuccess)
    assert "capabilities" in res.data  # type: ignore[operator]

    res = await service.browse_reference(_request("LIST_SERIES", limit=10))
    assert isinstance(res, BrowseReferenceSuccess)
    assert res.data["series"][0]["symbol"] == "EURUSD"  # type: ignore[index]

    res = await service.browse_reference(_request("LIST_INSTRUMENTS", limit=10))
    assert isinstance(res, BrowseReferenceSuccess)
    assert res.data["instruments"][0]["instrument"] == "EURUSD"  # type: ignore[index]

    res = await service.browse_reference(_request("LIST_BROKERS", limit=10))
    assert isinstance(res, BrowseReferenceSuccess)
    assert res.data["brokers"][0]["name"] == "MetaTrader 5"  # type: ignore[index]

    res = await service.browse_reference(_request("DISCOVER_SYMBOLS", limit=10))
    assert isinstance(res, BrowseReferenceSuccess)
    assert res.data["items"] == ["EURUSD"]  # type: ignore[index]

    res = await service.browse_reference(_request("READ_QUOTES", symbols=("EURUSD",)))
    assert isinstance(res, BrowseReferenceSuccess)
    assert len(res.data["rows"]) == 1  # type: ignore[index]

    res = await service.browse_reference(
        _request("READ_BARS", symbol="EURUSD", timeframe="H1", limit=10)
    )
    assert isinstance(res, BrowseReferenceSuccess)
    assert res.data["count"] == 2  # type: ignore[index]

    res = await service.browse_reference(_request("SYNC_REFERENCE"))
    assert isinstance(res, BrowseReferenceSuccess)
    assert res.data["series_synced"] == 1  # type: ignore[index]

    res = await service.browse_reference(
        _request("READ_INSTRUMENT", instrument="EURUSD")
    )
    assert isinstance(res, BrowseReferenceSuccess)
    assert res.data["instrument"] == "EURUSD"  # type: ignore[index]

    res = await service.browse_reference(_request("LIST_MARKET_DIRECTORY", limit=10))
    assert isinstance(res, BrowseReferenceSuccess)
    assert len(res.data["rows"]) == 1  # type: ignore[index]

    service.close()


@pytest.mark.asyncio
async def test_browse_reference_service_writes(tmp_path: Path) -> None:
    """Verify write operations against populated SQLite."""
    db_file = tmp_path / "test_writes.db"
    service = BrowseReferenceService(BrowseReferenceConfig(database_path=str(db_file)))
    _seed_test_db(service)

    res = await service.browse_reference(
        _request(
            "UPDATE_INSTRUMENT", instrument="EURUSD", payload={"default_spread": 2.5}
        )
    )
    assert isinstance(res, BrowseReferenceSuccess)
    assert res.data["default_spread"] == 2.5  # type: ignore[index]

    res = await service.browse_reference(
        _request(
            "UPDATE_SERIES",
            series_id=1,
            payload={"symbol": "EURUSD", "instrument": "EURUSD", "show": 0},
        )
    )
    assert isinstance(res, BrowseReferenceSuccess)
    assert res.data["series_id"] == 1  # type: ignore[index]

    service.close()


@pytest.mark.asyncio
async def test_browse_reference_errors(tmp_path: Path) -> None:
    """Verify error mappings for not found and validation failures."""
    db_file = tmp_path / "empty.db"
    service = BrowseReferenceService(BrowseReferenceConfig(database_path=str(db_file)))

    # Missing bars
    bars_err = await service.browse_reference(
        _request("READ_BARS", symbol="NOSUCH", timeframe="H1")
    )
    assert isinstance(bars_err, DataFailure)
    assert bars_err.problem.status == 503

    # Missing instrument
    inst_err = await service.browse_reference(
        _request("READ_INSTRUMENT", instrument="NOSUCH")
    )
    assert isinstance(inst_err, DataFailure)
    assert inst_err.problem.status == 404

    # Missing series
    series_err = await service.browse_reference(
        _request(
            "UPDATE_SERIES",
            series_id=999,
            payload={"symbol": "EURUSD", "instrument": "EURUSD"},
        )
    )
    assert isinstance(series_err, DataFailure)
    assert series_err.problem.status == 404

    # Invalid series update (missing symbol)
    val_err = await service.browse_reference(
        _request("UPDATE_SERIES", series_id=1, payload={})
    )
    assert isinstance(val_err, DataFailure)
    assert val_err.problem.status == 422

    # Unknown operation
    unk_req = BrowseReferenceRequest.model_construct(
        request_id=str(uuid7()),
        operation="UNKNOWN_OP",
    )
    unk_err = await service.browse_reference(unk_req)
    assert isinstance(unk_err, DataFailure)
    assert unk_err.problem.status == 400

    service.close()
