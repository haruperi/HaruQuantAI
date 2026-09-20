"""Tests for FEAT-DATA-UNIVERSES (app/services/data/universes.py)."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from pathlib import Path

import pytest
from app.contracts.data import (
    BasketConstituent,
    DataError,
    UniverseBasket,
)
from app.services.data.universes import (
    UniverseConfig,
    UniverseManagerServiceImpl,
)
from app.services.persistence.data import (
    DataPersistenceConfig,
    DataPersistenceServiceImpl,
)
from app.services.persistence.database import (
    DatabaseConfig,
    DatabaseServiceImpl,
)


async def _setup_universes(tmp_path: Path) -> UniverseManagerServiceImpl:
    db_file = tmp_path / "test_universes.db"
    db = DatabaseServiceImpl(DatabaseConfig(database_path=db_file))
    persist = DataPersistenceServiceImpl(
        db, DataPersistenceConfig(preseed_defaults=True)
    )
    await persist.initialize_schema()
    return UniverseManagerServiceImpl(persist, UniverseConfig())


def test_point_in_time_constituent_tracking(tmp_path: Path) -> None:
    """Verify point-in-time historical constituent filtering."""

    async def _test() -> None:
        svc = await _setup_universes(tmp_path)

        # Basket with constituents joining and leaving at different times
        basket = UniverseBasket(
            name="SP500_Sample",
            description="Sample index with member rotation",
            is_system=False,
            constituents=[
                # TSLA joined on 2020-12-21
                BasketConstituent(
                    symbol="TSLA",
                    date_from=datetime(2020, 12, 21, tzinfo=UTC),
                ),
                # OLD_STOCK left on 2020-12-20
                BasketConstituent(
                    symbol="OLD_STOCK",
                    date_to=datetime(2020, 12, 20, tzinfo=UTC),
                ),
                # AAPL always present
                BasketConstituent(symbol="AAPL"),
            ],
        )
        saved = await svc.save_basket(basket)

        # 1. As of 2020-01-01 (Before TSLA joined, while OLD_STOCK active)
        const_2020 = await svc.get_point_in_time_constituents(
            saved.id, as_of=datetime(2020, 1, 1, tzinfo=UTC)
        )
        assert "AAPL" in const_2020
        assert "OLD_STOCK" in const_2020
        assert "TSLA" not in const_2020

        # 2. As of 2021-01-01 (After TSLA joined, after OLD_STOCK left)
        const_2021 = await svc.get_point_in_time_constituents(
            saved.id, as_of=datetime(2021, 1, 1, tzinfo=UTC)
        )
        assert "AAPL" in const_2021
        assert "TSLA" in const_2021
        assert "OLD_STOCK" not in const_2021

    asyncio.run(_test())


def test_system_basket_protection(tmp_path: Path) -> None:
    """Verify system universe baskets cannot be deleted."""

    async def _test() -> None:
        svc = await _setup_universes(tmp_path)

        sys_basket = UniverseBasket(
            name="Protected_System_Basket",
            is_system=True,
            constituents=[BasketConstituent(symbol="EURUSD")],
        )
        saved = await svc.save_basket(sys_basket)

        with pytest.raises(DataError, match="Cannot delete system"):
            await svc.delete_basket(saved.id)

        # Custom basket can be deleted
        custom = UniverseBasket(name="Custom_Basket", is_system=False)
        saved_custom = await svc.save_basket(custom)
        assert await svc.delete_basket(saved_custom.id) is True

    asyncio.run(_test())
