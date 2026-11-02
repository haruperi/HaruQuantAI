"""Tests for CorrelationOf catalog, period bucketing, and Pearson correlation."""

from __future__ import annotations

from collections.abc import Sequence
from typing import override

import pytest
from app.extend.correlation_of import (
    DATA_TYPE_PL,
    DATA_TYPE_TRADES,
    CorrelationOfCatalog,
    CorrelationOrderRecord,
    CorrelationPeriod,
    CorrelationType,
    Loss,
    NumberOfClosedPositions,
    NumberOfClosedTrades,
    NumberOfOpenPositions,
    NumberOfOpenTrades,
    ProfitLoss,
    TimePeriod,
    get_period_bucket,
    next_period_bucket,
)


class TestCorrelationOfCatalog:
    """Test suite for CorrelationOfCatalog and modular correlation snippets."""

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


class TestIndividualCorrelationSnippets:
    """Test suite validating direct snippet classes matching SQ donor files."""

    def test_loss_snippet(self) -> None:
        """Assert Loss attributes, compute_periods, and should_skip_period behavior."""
        loss_metric = Loss()
        assert loss_metric.name == "Loss"
        assert loss_metric.data_type == DATA_TYPE_PL

        # Non-loss periods are skipped: both >= 0
        assert loss_metric.should_skip_period(0.0, 50.0) is True
        assert loss_metric.should_skip_period(100.0, 200.0) is True
        # If at least one has a loss, do not skip
        assert loss_metric.should_skip_period(-10.0, 50.0) is False
        assert loss_metric.should_skip_period(-10.0, -20.0) is False

        orders = [
            CorrelationOrderRecord(
                open_time_ms=1000,
                close_time_ms=2000,
                profit_loss=-50.0,
                is_canceled=False,
            ),
            CorrelationOrderRecord(
                open_time_ms=1000,
                close_time_ms=2000,
                profit_loss=100.0,
                is_canceled=True,  # Canceled order skipped
            ),
        ]
        res = loss_metric.compute_periods(orders, "DAY")
        b = get_period_bucket(2000, "DAY")
        assert res[b] == -50.0

    def test_number_of_closed_positions_snippet(self) -> None:
        """Assert NumberOfClosedPositions long (+1) and short (-1) accumulation."""
        pos_metric = NumberOfClosedPositions()
        assert pos_metric.name == "Number of closed positions"
        assert pos_metric.data_type == DATA_TYPE_TRADES
        assert pos_metric.should_skip_period(0.0, 0.0) is False

        orders = [
            CorrelationOrderRecord(
                open_time_ms=1000,
                close_time_ms=2000,
                profit_loss=10.0,
                is_long=True,
            ),
            CorrelationOrderRecord(
                open_time_ms=1000,
                close_time_ms=2000,
                profit_loss=5.0,
                is_long=False,
            ),
            CorrelationOrderRecord(
                open_time_ms=1000,
                close_time_ms=2000,
                profit_loss=5.0,
                is_long=False,
                is_canceled=True,
            ),
        ]
        res = pos_metric.compute_periods(orders, "DAY")
        b = get_period_bucket(2000, "DAY")
        assert res[b] == 0.0  # +1 (long) - 1 (short)

    def test_number_of_closed_trades_snippet(self) -> None:
        """Assert NumberOfClosedTrades counts all closed trades."""
        trades_metric = NumberOfClosedTrades()
        assert trades_metric.name == "Number of closed trades"
        assert trades_metric.data_type == DATA_TYPE_TRADES

        orders = [
            CorrelationOrderRecord(
                open_time_ms=1000,
                close_time_ms=2000,
                profit_loss=10.0,
                is_long=False,
            ),
            CorrelationOrderRecord(
                open_time_ms=1000,
                close_time_ms=2000,
                profit_loss=20.0,
                is_long=True,
            ),
            CorrelationOrderRecord(
                open_time_ms=1000,
                close_time_ms=2000,
                profit_loss=30.0,
                is_canceled=True,
            ),
        ]
        res = trades_metric.compute_periods(orders, "DAY")
        b = get_period_bucket(2000, "DAY")
        assert res[b] == 2.0

    def test_number_of_open_positions_snippet(self) -> None:
        """Assert NumberOfOpenPositions accumulates across overlapping active periods."""
        open_pos_metric = NumberOfOpenPositions()
        assert open_pos_metric.name == "Number of open positions"
        assert open_pos_metric.data_type == DATA_TYPE_TRADES

        t_open = 1767225600000  # 2026-01-01 00:00:00
        t_close = 1767398400000  # 2026-01-03 00:00:00
        orders = [
            CorrelationOrderRecord(
                open_time_ms=t_open,
                close_time_ms=t_close,
                profit_loss=0.0,
                is_long=False,  # Short -> -1.0
            ),
            CorrelationOrderRecord(
                open_time_ms=t_open,
                close_time_ms=t_close,
                profit_loss=0.0,
                is_long=True,
                is_canceled=True,  # Canceled -> ignored
            ),
        ]
        res = open_pos_metric.compute_periods(orders, "DAY")
        assert len(res) == 2
        for val in res.values():
            assert val == -1.0

    def test_number_of_open_trades_snippet(self) -> None:
        """Assert NumberOfOpenTrades accumulates across overlapping active periods."""
        open_trades_metric = NumberOfOpenTrades()
        assert open_trades_metric.name == "Number of open trades"
        assert open_trades_metric.data_type == DATA_TYPE_TRADES

        t_open = 1767225600000
        t_close = 1767398400000
        orders = [
            CorrelationOrderRecord(
                open_time_ms=t_open,
                close_time_ms=t_close,
                profit_loss=0.0,
                is_long=False,
            ),
            CorrelationOrderRecord(
                open_time_ms=t_open,
                close_time_ms=t_close,
                profit_loss=0.0,
                is_long=True,
                is_canceled=True,
            ),
        ]
        res = open_trades_metric.compute_periods(orders, "DAY")
        assert len(res) == 2
        for val in res.values():
            assert val == 1.0

    def test_profit_loss_snippet(self) -> None:
        """Assert ProfitLoss snippet accumulates signed P/L."""
        pl_metric = ProfitLoss()
        assert pl_metric.name == "Profit/Loss"
        assert pl_metric.data_type == DATA_TYPE_PL
        assert pl_metric.should_skip_period(10.0, 20.0) is False

        orders = [
            CorrelationOrderRecord(
                open_time_ms=1000,
                close_time_ms=2000,
                profit_loss=125.5,
            ),
            CorrelationOrderRecord(
                open_time_ms=1000,
                close_time_ms=2000,
                profit_loss=-25.5,
            ),
        ]
        res = pl_metric.compute_periods(orders, "DAY")
        b = get_period_bucket(2000, "DAY")
        assert res[b] == 100.0

    def test_time_period_and_base_methods(self) -> None:
        """Assert TimePeriod dataclass and base method behavior."""
        tp = TimePeriod(from_ms=1000, to_ms=2000, value=42.0)
        assert tp.from_ms == 1000
        assert tp.to_ms == 2000
        assert tp.value == 42.0

        # Subclass CorrelationType for base method testing
        class CustomCorrelation(CorrelationType):
            @override
            def compute_periods(
                self,
                orders: Sequence[CorrelationOrderRecord],
                period: CorrelationPeriod,
                periods: dict[int, float] | None = None,
            ) -> dict[int, float]:
                return {}

        custom = CustomCorrelation("Custom", DATA_TYPE_PL)
        assert custom.name == "Custom"
        assert custom.data_type == DATA_TYPE_PL
        assert custom.should_skip_period(1.0, 2.0) is False

        order = CorrelationOrderRecord(
            open_time_ms=1000,
            close_time_ms=2000,
            profit_loss=0.0,
            is_canceled=True,
        )
        assert custom.is_canceled_order(order) is True

    def test_next_period_bucket_invalid(self) -> None:
        """Assert next_period_bucket raises ValueError on invalid period."""
        with pytest.raises(ValueError, match=r"^Unknown correlation period: INVALID$"):
            next_period_bucket(1000, "INVALID")  # type: ignore[arg-type]
