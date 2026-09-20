"""Tests for FEAT-DATA-INSTRUMENTS (app/services/data/instruments.py)."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from app.contracts.data import (
    InstrumentDefinition,
    InvalidInstrumentError,
)
from app.services.data.instruments import (
    InstrumentCatalogConfig,
    InstrumentCatalogImpl,
)
from app.services.persistence.data import (
    DataPersistenceConfig,
    DataPersistenceServiceImpl,
)
from app.services.persistence.database import (
    DatabaseConfig,
    DatabaseServiceImpl,
)


async def _setup_catalog(tmp_path: Path) -> InstrumentCatalogImpl:
    db_file = tmp_path / "test_inst_cat.db"
    db = DatabaseServiceImpl(DatabaseConfig(database_path=db_file))
    persist = DataPersistenceServiceImpl(
        db, DataPersistenceConfig(preseed_defaults=True)
    )
    await persist.initialize_schema()
    return InstrumentCatalogImpl(persist, InstrumentCatalogConfig())


def test_instrument_validation_rules(tmp_path: Path) -> None:
    """Verify mathematical and financial constraint validation."""

    async def _test() -> None:
        cat = await _setup_catalog(tmp_path)

        # Valid instrument
        valid_inst = InstrumentDefinition(
            symbol="EURUSD",
            tick_size=0.00001,
            tick_step=0.00001,
            point_value=100000.0,
            decimals=5,
            min_volume=0.01,
            max_volume=100.0,
            lot_step=0.01,
            margin_rate=0.0333,
        )
        res = cat.validate_instrument(valid_inst)
        assert res.is_valid is True
        assert len(res.errors) == 0

        # Invalid instrument (negative tick_size, max_volume < min_volume)
        invalid_inst = InstrumentDefinition(
            symbol="BAD_SYM",
            tick_size=-0.01,
            point_value=0.0,
            min_volume=10.0,
            max_volume=1.0,
            margin_rate=-0.5,
            swap_3day_day=10,
        )
        bad_res = cat.validate_instrument(invalid_inst)
        assert bad_res.is_valid is False
        assert len(bad_res.errors) >= 4

    asyncio.run(_test())


def test_strict_validation_guard(tmp_path: Path) -> None:
    """Verify that saving an invalid instrument raises InvalidInstrumentError."""

    async def _test() -> None:
        cat = await _setup_catalog(tmp_path)
        bad_inst = InstrumentDefinition(
            symbol="FAIL",
            tick_size=-1.0,
        )
        with pytest.raises(InvalidInstrumentError):
            await cat.save_instrument(bad_inst)

    asyncio.run(_test())


def test_alias_resolution(tmp_path: Path) -> None:
    """Verify alias mapping and transparent instrument retrieval."""

    async def _test() -> None:
        cat = await _setup_catalog(tmp_path)

        # Register alias EUR/USD -> EURUSD
        await cat.add_alias("EURUSD", "EUR/USD", broker_id=1, notes="Test alias")

        # Resolve
        canonical = await cat.resolve_alias("EUR/USD", broker_id=1)
        assert canonical == "EURUSD"

        # Direct instrument fetch by alias
        inst = await cat.get_instrument("EUR/USD")
        assert inst is not None
        assert inst.symbol == "EURUSD"

    asyncio.run(_test())
