"""Tests for CorrelationOf catalog, period bucketing, and Pearson correlation."""

from __future__ import annotations

import pytest
from app.extend.correlation_of.catalog import (
    CorrelationOfCatalog,
    CorrelationOrderRecord,
)


class TestCorrelationOfCatalog:
    """Test suite for CorrelationOfCatalog."""

    def test_golden_fixtures(self) -> None:
        """Assert exact golden fixtures from normative work order."""
        # Golden fixture 1: Loss skips periods where both >= 0
        series_loss_a = {1000: -50.0, 2000: 100.0, 3000: -25.0}
        series_loss_b = {1000: -100.0, 2000: 80.0, 3000: -50.0}
        r_loss = CorrelationOfCatalog.pearson("Loss", series_loss_a, series_loss_b)
        assert r_loss == 1.0

        # Golden fixture 2: ProfitLoss identical series
        series_pl = {1000: 10.0, 2000: -5.0, 3000: 20.0}
        r_pl = CorrelationOfCatalog.pearson("ProfitLoss", series_pl, series_pl)
        assert r_pl == 1.0

    def test_definitions(self) -> None:
        """Assert all 6 expected definitions are registered."""
        defs = CorrelationOfCatalog.definitions()
        assert defs == frozenset(
            {
                "ProfitLoss",
                "Loss",
                "NumberOfClosedTrades",
                "NumberOfOpenTrades",
                "NumberOfClosedPositions",
                "NumberOfOpenPositions",
            }
        )

    def test_compute_periods_closed_metrics(self) -> None:
        """Assert compute_periods correctly aggregates close-time metrics."""
        # Orders on 2026-01-01 (epoch ms ~1767225600000)
        t_open = 1767225600000  # 2026-01-01 00:00:00 UTC
        t_close_day1 = 1767230000000  # 2026-01-01 01:13:20 UTC
        t_close_day2 = 1767320000000  # 2026-01-02 02:13:20 UTC

        orders = [
            CorrelationOrderRecord(
                open_time_ms=t_open,
                close_time_ms=t_close_day1,
                profit_loss=150.0,
                is_long=True,
            ),
            CorrelationOrderRecord(
                open_time_ms=t_open,
                close_time_ms=t_close_day1,
                profit_loss=-50.0,
                is_long=False,
            ),
            CorrelationOrderRecord(
                open_time_ms=t_open,
                close_time_ms=t_close_day2,
                profit_loss=200.0,
                is_canceled=True,  # Canceled order should be skipped
            ),
            CorrelationOrderRecord(
                open_time_ms=t_open,
                close_time_ms=t_close_day2,
                profit_loss=-80.0,
                is_long=True,
            ),
        ]

        # ProfitLoss
        pl_buckets = CorrelationOfCatalog.compute_periods(
            "ProfitLoss", orders, period="DAY"
        )
        assert len(pl_buckets) == 2
        b1, b2 = sorted(pl_buckets.keys())
        assert pl_buckets[b1] == 100.0  # 150 - 50
        assert pl_buckets[b2] == -80.0  # -80 (canceled 200 skipped)

        # NumberOfClosedTrades
        trades_buckets = CorrelationOfCatalog.compute_periods(
            "NumberOfClosedTrades", orders, period="DAY"
        )
        assert trades_buckets[b1] == 2.0
        assert trades_buckets[b2] == 1.0

        # NumberOfClosedPositions (long=+1, short=-1)
        pos_buckets = CorrelationOfCatalog.compute_periods(
            "NumberOfClosedPositions", orders, period="DAY"
        )
        assert pos_buckets[b1] == 0.0  # +1 (long) - 1 (short)
        assert pos_buckets[b2] == 1.0  # +1 (long)

    def test_compute_periods_open_metrics(self) -> None:
        """Assert compute_periods correctly aggregates overlapping open metrics."""
        t1 = 1767225600000  # 2026-01-01 00:00:00
        t2 = 1767398400000  # 2026-01-03 00:00:00

        # Order spanning day 1 and day 2
        orders = [
            CorrelationOrderRecord(
                open_time_ms=t1,
                close_time_ms=t2,
                profit_loss=50.0,
                is_long=True,
            ),
        ]

        open_trades = CorrelationOfCatalog.compute_periods(
            "NumberOfOpenTrades", orders, period="DAY"
        )
        # Should be active on 2026-01-01 and 2026-01-02
        assert len(open_trades) == 2
        for val in open_trades.values():
            assert val == 1.0

        open_pos = CorrelationOfCatalog.compute_periods(
            "NumberOfOpenPositions", orders, period="DAY"
        )
        assert len(open_pos) == 2
        for val in open_pos.values():
            assert val == 1.0

    def test_pearson_edge_cases(self) -> None:
        """Assert zero variance, empty periods, and small sample edge cases."""
        # Fewer than 2 pairs
        assert CorrelationOfCatalog.pearson("ProfitLoss", {1: 10.0}, {1: 20.0}) == 0.0

        # Zero variance
        assert (
            CorrelationOfCatalog.pearson(
                "ProfitLoss", {1: 5.0, 2: 5.0}, {1: 10.0, 2: 20.0}
            )
            == 0.0
        )

        # Allow empty periods vs omit empty periods
        s_a = {1: 10.0, 2: 0.0, 3: 20.0}
        s_b = {1: 5.0, 2: 0.0, 3: 15.0}
        r_omitted = CorrelationOfCatalog.pearson(
            "ProfitLoss", s_a, s_b, allow_empty_periods=False
        )
        r_retained = CorrelationOfCatalog.pearson(
            "ProfitLoss", s_a, s_b, allow_empty_periods=True
        )
        assert r_omitted == 1.0
        assert 0.98 <= r_retained <= 1.0

    def test_invalid_definition_and_period(self) -> None:
        """Assert unknown definition and period raise ValueError."""
        with pytest.raises(
            ValueError, match=r"^Unknown correlation definition: Unknown$"
        ):
            CorrelationOfCatalog.compute_periods("Unknown", [])

        with pytest.raises(ValueError, match=r"^Unknown correlation period: INVALID$"):
            CorrelationOfCatalog.compute_periods(
                "ProfitLoss",
                [
                    CorrelationOrderRecord(
                        open_time_ms=1000, close_time_ms=2000, profit_loss=10.0
                    )
                ],
                period="INVALID",  # type: ignore[arg-type]
            )

    def test_all_period_granularities(self) -> None:
        """Assert period bucketing works across HOUR, WEEK, MONTH, YEAR."""
        t1 = 1767225600000  # 2026-01-01 00:00:00
        t2 = 1798761600000  # 2027-01-01 00:00:00
        orders = [
            CorrelationOrderRecord(
                open_time_ms=t1, close_time_ms=t1 + 3600000, profit_loss=10.0
            ),
            CorrelationOrderRecord(
                open_time_ms=t2, close_time_ms=t2 + 3600000, profit_loss=20.0
            ),
        ]
        for p in ["HOUR", "WEEK", "MONTH", "YEAR"]:
            buckets = CorrelationOfCatalog.compute_periods(
                "ProfitLoss",
                orders,
                period=p,  # type: ignore[arg-type]
            )
            assert len(buckets) >= 1

        # Test open trades across periods
        open_orders = [
            CorrelationOrderRecord(
                open_time_ms=t1, close_time_ms=t1 + 7200000, profit_loss=10.0
            ),
        ]
        for p in ["HOUR", "WEEK", "MONTH", "YEAR"]:
            open_buckets = CorrelationOfCatalog.compute_periods(
                "NumberOfOpenTrades",
                open_orders,
                period=p,  # type: ignore[arg-type]
            )
            assert len(open_buckets) >= 1
