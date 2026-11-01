"""Unit tests for strategy checkers."""

from app.extend.checker.checkers import (
    ComparisonChecker,
    IndicatorFastSlowChecker,
    PropertyChecker,
)


class TestCheckers:
    """Test suite for ComparisonChecker, IndicatorFastSlowChecker, and PropertyChecker."""

    def test_comparison_checker(self) -> None:
        """Assert ComparisonChecker handles standard operators."""
        assert ComparisonChecker.check(10.0, "<", 20.0) is True
        assert ComparisonChecker.check(20.0, "<", 10.0) is False
        assert ComparisonChecker.check(10.0, "<=", 10.0) is True
        assert ComparisonChecker.check(15.0, ">", 10.0) is True
        assert ComparisonChecker.check(10.0, ">=", 10.0) is True
        assert ComparisonChecker.check(10.0, "==", 10.0) is True
        assert ComparisonChecker.check(10.0, "!=", 12.0) is True
        assert ComparisonChecker.check(10.0, "invalid", 10.0) is False  # type: ignore[arg-type]

    def test_indicator_fast_slow_golden_fixtures(self) -> None:
        """Assert golden fixtures: 12 < 26 is True, 30 < 20 is False."""
        assert (
            IndicatorFastSlowChecker.check({"FastPeriod": 12, "SlowPeriod": 26}) is True
        )
        assert (
            IndicatorFastSlowChecker.check({"FastPeriod": 30, "SlowPeriod": 20})
            is False
        )
        assert (
            IndicatorFastSlowChecker.check({"FastPeriod": 20, "SlowPeriod": 20})
            is False
        )

        # Missing pair keys don't fail
        assert IndicatorFastSlowChecker.check({"FastPeriod": 12}) is True
        assert IndicatorFastSlowChecker.check({}) is True

    def test_property_checker(self) -> None:
        """Assert PropertyChecker matches required keys and values."""
        strategy = {"Symbol": "EURUSD", "Timeframe": "H1", "Type": "Trend"}
        assert PropertyChecker.check(strategy, {"Symbol": "EURUSD"}) is True
        assert (
            PropertyChecker.check(strategy, {"Symbol": "EURUSD", "Timeframe": "H1"})
            is True
        )
        assert PropertyChecker.check(strategy, {"Symbol": "GBPUSD"}) is False
        assert PropertyChecker.check(strategy, {"MissingKey": 123}) is False
