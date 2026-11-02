"""Unit tests for strategy checkers, AST verification, and legacy fixtures."""

from __future__ import annotations

import xml.etree.ElementTree as ET

from app.extend.checker.base import (
    element_to_string,
    find_all_items,
    parse_element,
)
from app.extend.checker.checkers import (
    ComparisonChecker,
    IndicatorFastSlowChecker,
    PropertyChecker,
)


class TestCheckersLegacy:
    """Test suite preserving legacy scalar and dict interfaces."""

    def test_comparison_checker_scalar(self) -> None:
        """Assert ComparisonChecker handles standard scalar operators."""
        assert ComparisonChecker.check(10.0, "<", 20.0) is True
        assert ComparisonChecker.check(20.0, "<", 10.0) is False
        assert ComparisonChecker.check(10.0, "<=", 10.0) is True
        assert ComparisonChecker.check(15.0, ">", 10.0) is True
        assert ComparisonChecker.check(10.0, ">=", 10.0) is True
        assert ComparisonChecker.check(10.0, "==", 10.0) is True
        assert ComparisonChecker.check(10.0, "!=", 12.0) is True
        assert ComparisonChecker.check(10.0, "invalid", 10.0) is False

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

    def test_property_checker_dict(self) -> None:
        """Assert PropertyChecker matches required keys and values."""
        strategy = {"Symbol": "EURUSD", "Timeframe": "H1", "Type": "Trend"}
        assert PropertyChecker.check(strategy, {"Symbol": "EURUSD"}) is True
        assert (
            PropertyChecker.check(strategy, {"Symbol": "EURUSD", "Timeframe": "H1"})
            is True
        )
        assert PropertyChecker.check(strategy, {"Symbol": "GBPUSD"}) is False
        assert PropertyChecker.check(strategy, {"MissingKey": 123}) is False


class TestBaseHelpers:
    """Test suite for base XML parsing and traversal helpers."""

    def test_parse_element(self) -> None:
        """Test parse_element with Element, string, and invalid data."""
        elem = ET.Element("Root")
        assert parse_element(elem) is elem
        parsed = parse_element("<Item key='test'/>")
        assert parsed is not None
        assert parsed.attrib.get("key") == "test"
        assert parse_element("<invalid xml") is None
        assert parse_element(12345) is None

    def test_element_to_string_and_find_all(self) -> None:
        """Test XML serialization and recursive Item retrieval."""
        root = ET.fromstring("<Root><Item key='1'><Item key='2'/></Item></Root>")
        xml_str = element_to_string(root)
        assert "<Root>" in xml_str
        items = find_all_items(root)
        assert len(items) == 2


class TestComparisonCheckerAST:
    """Test suite for ComparisonChecker AST element verification."""

    def test_unparseable_element(self) -> None:
        """Assert unparseable element returns False."""
        assert ComparisonChecker.check_block(None) is False
        assert ComparisonChecker.check_block("<bad xml") is False

    def test_skip_non_boolean_return_type(self) -> None:
        """Assert blocks with non-boolean returnType are skipped (return True)."""
        xml = "<Item returnType='number' key='Add'/>"
        assert ComparisonChecker.check(xml) is True

    def test_not_block_validation(self) -> None:
        """Assert Not block handles boolean vs non-boolean return types."""
        # Non-Not block with no Left/Right is skipped
        xml_other = "<Item returnType='boolean' key='OtherBlock'/>"
        assert ComparisonChecker.check(xml_other) is True

        # Not block with no #Value# is skipped
        xml_not_no_val = "<Item returnType='boolean' key='Not'/>"
        assert ComparisonChecker.check(xml_not_no_val) is True

        # Not block with boolean #Value# passes
        xml_not_bool = (
            "<Item returnType='boolean' key='Not'>"
            "<Param key='#Value#'><Item returnType='boolean'/></Param>"
            "</Item>"
        )
        assert ComparisonChecker.check(xml_not_bool) is True

        # Not block with number #Value# fails
        xml_not_num = (
            "<Item returnType='boolean' key='Not'>"
            "<Param key='#Value#'><Item returnType='number'/></Param>"
            "</Item>"
        )
        assert ComparisonChecker.check(xml_not_num) is False

    def test_left_right_same_fails(self) -> None:
        """Assert comparing identical left and right expressions fails."""
        xml = (
            "<Item returnType='boolean' key='Greater'>"
            "<Param key='#Left#'><Item key='RSI' returnType='number'/></Param>"
            "<Param key='#Right#'><Item key='RSI' returnType='number'/></Param>"
            "</Item>"
        )
        assert ComparisonChecker.check(xml) is False

    def test_different_return_types_fails(self) -> None:
        """Assert comparing operands with different return types fails."""
        xml = (
            "<Item returnType='boolean' key='Greater'>"
            "<Param key='#Left#'><Item key='A' returnType='number'/></Param>"
            "<Param key='#Right#'><Item key='B' returnType='boolean'/></Param>"
            "</Item>"
        )
        assert ComparisonChecker.check(xml) is False

    def test_indicator_vs_indicator(self) -> None:
        """Assert comparing different number indicators fails, same indicator passes."""
        # Different indicators fail
        xml_diff = (
            "<Item returnType='boolean' key='Greater'>"
            "<Param key='#Left#'><Item key='CCI' returnType='number' categoryType='indicator'/></Param>"
            "<Param key='#Right#'><Item key='RSI' returnType='number' categoryType='indicator'/></Param>"
            "</Item>"
        )
        assert ComparisonChecker.check(xml_diff) is False

        # Same indicator with different parameters passes
        xml_same = (
            "<Item returnType='boolean' key='Greater'>"
            "<Param key='#Left#'><Item key='RSI' returnType='number' categoryType='indicator'><Param key='#Period#'>14</Param></Item></Param>"
            "<Param key='#Right#'><Item key='RSI' returnType='number' categoryType='indicator'><Param key='#Period#'>28</Param></Item></Param>"
            "</Item>"
        )
        assert ComparisonChecker.check(xml_same) is True

    def test_indicator_vs_other(self) -> None:
        """Assert indicator compared with non-Number fails, with Number passes."""
        xml_valid = (
            "<Item returnType='boolean' key='Greater'>"
            "<Param key='#Left#'><Item key='RSI' returnType='number' categoryType='indicator'/></Param>"
            "<Param key='#Right#'><Item key='Number' returnType='number' categoryType='other'><Param>70</Param></Item></Param>"
            "</Item>"
        )
        assert ComparisonChecker.check(xml_valid) is True

        xml_invalid = (
            "<Item returnType='boolean' key='Greater'>"
            "<Param key='#Left#'><Item key='RSI' returnType='number' categoryType='indicator'/></Param>"
            "<Param key='#Right#'><Item key='Custom' returnType='number' categoryType='other'/></Param>"
            "</Item>"
        )
        assert ComparisonChecker.check(xml_invalid) is False

        # Reverse order: other vs indicator
        xml_rev_valid = (
            "<Item returnType='boolean' key='Greater'>"
            "<Param key='#Left#'><Item key='Number' returnType='number' categoryType='other'><Param>30</Param></Item></Param>"
            "<Param key='#Right#'><Item key='RSI' returnType='number' categoryType='indicator'/></Param>"
            "</Item>"
        )
        assert ComparisonChecker.check(xml_rev_valid) is True

        xml_rev_invalid = (
            "<Item returnType='boolean' key='Greater'>"
            "<Param key='#Left#'><Item key='Custom' returnType='number' categoryType='other'/></Param>"
            "<Param key='#Right#'><Item key='RSI' returnType='number' categoryType='indicator'/></Param>"
            "</Item>"
        )
        assert ComparisonChecker.check(xml_rev_invalid) is False

    def test_bar_time_comparisons(self) -> None:
        """Assert bar time blocks must be on left and within valid numerical ranges."""
        # Time block on right with Number on left fails
        xml_right_time = (
            "<Item returnType='boolean' key='Greater'>"
            "<Param key='#Left#'><Item key='Number' returnType='number' categoryType='other'><Param>10</Param></Item></Param>"
            "<Param key='#Right#'><Item key='BarHour' returnType='number' categoryType='other'/></Param>"
            "</Item>"
        )
        assert ComparisonChecker.check(xml_right_time) is False

        # Valid Hour comparison
        xml_valid_hour = (
            "<Item returnType='boolean' key='Greater'>"
            "<Param key='#Left#'><Item key='BarHour' returnType='number' categoryType='other'/></Param>"
            "<Param key='#Right#'><Item key='Number' returnType='number' categoryType='other'><Param>15</Param></Item></Param>"
            "</Item>"
        )
        assert ComparisonChecker.check(xml_valid_hour) is True

        # Invalid Hour (< 0 or > 23)
        xml_bad_hour = (
            "<Item returnType='boolean' key='Greater'>"
            "<Param key='#Left#'><Item key='BarHour' returnType='number' categoryType='other'/></Param>"
            "<Param key='#Right#'><Item key='Number' returnType='number' categoryType='other'><Param>25</Param></Item></Param>"
            "</Item>"
        )
        assert ComparisonChecker.check(xml_bad_hour) is False

        # Invalid Minute (< 0 or > 59)
        xml_bad_min = (
            "<Item returnType='boolean' key='Greater'>"
            "<Param key='#Left#'><Item key='BarMinute' returnType='number' categoryType='other'/></Param>"
            "<Param key='#Right#'><Item key='Number' returnType='number' categoryType='other'><Param>65</Param></Item></Param>"
            "</Item>"
        )
        assert ComparisonChecker.check(xml_bad_min) is False

        # Invalid DayOfWeek (< 0 or > 6)
        xml_bad_dow = (
            "<Item returnType='boolean' key='Greater'>"
            "<Param key='#Left#'><Item key='BarDayOfWeek' returnType='number' categoryType='other'/></Param>"
            "<Param key='#Right#'><Item key='Number' returnType='number' categoryType='other'><Param>7</Param></Item></Param>"
            "</Item>"
        )
        assert ComparisonChecker.check(xml_bad_dow) is False

        # Crosses comparison on bar time blocks is disallowed
        xml_crosses = (
            "<Item returnType='boolean' key='CrossesAbove'>"
            "<Param key='#Left#'><Item key='BarHour' returnType='number' categoryType='other'/></Param>"
            "<Param key='#Right#'><Item key='Number' returnType='number' categoryType='other'><Param>10</Param></Item></Param>"
            "</Item>"
        )
        assert ComparisonChecker.check(xml_crosses) is False

        # Other on left that is not bar time when Right is Number fails
        xml_non_time = (
            "<Item returnType='boolean' key='Greater'>"
            "<Param key='#Left#'><Item key='SomethingElse' returnType='number' categoryType='other'/></Param>"
            "<Param key='#Right#'><Item key='Number' returnType='number' categoryType='other'><Param>10</Param></Item></Param>"
            "</Item>"
        )
        assert ComparisonChecker.check(xml_non_time) is False

        # Comparing two bar time blocks fails
        xml_two_time = (
            "<Item returnType='boolean' key='Greater'>"
            "<Param key='#Left#'><Item key='BarHour' returnType='number' categoryType='other'/></Param>"
            "<Param key='#Right#'><Item key='BarMinute' returnType='number' categoryType='other'/></Param>"
            "</Item>"
        )
        assert ComparisonChecker.check(xml_two_time) is False

    def test_hhmm_time_validation(self) -> None:
        """Assert HighestInRange and LowestInRange validate HHMM time format."""
        # Valid HHMM
        xml_valid_hhmm = (
            "<Item returnType='boolean' key='Greater'>"
            "<Param key='#Left#'><Item key='HighestInRange' returnType='price'>"
            "<Param key='#TimeFrom#'>930</Param><Param key='#TimeTo#'>1600</Param></Item></Param>"
            "<Param key='#Right#'><Item key='LowestInRange' returnType='price'>"
            "<Param key='#TimeFrom#'>800</Param><Param key='#TimeTo#'>1500</Param></Item></Param>"
            "</Item>"
        )
        assert ComparisonChecker.check(xml_valid_hhmm) is True

        # Bad hour (2430)
        xml_bad_hh = (
            "<Item returnType='boolean' key='Greater'>"
            "<Param key='#Left#'><Item key='HighestInRange' returnType='price'>"
            "<Param key='#TimeFrom#'>2430</Param></Item></Param>"
            "<Param key='#Right#'><Item key='Close' returnType='price'/></Param>"
            "</Item>"
        )
        assert ComparisonChecker.check(xml_bad_hh) is False

        # Bad minute (1265)
        xml_bad_mm = (
            "<Item returnType='boolean' key='Greater'>"
            "<Param key='#Left#'><Item key='LowestInRange' returnType='price'>"
            "<Param key='#TimeTo#'>1265</Param></Item></Param>"
            "<Param key='#Right#'><Item key='Close' returnType='price'/></Param>"
            "</Item>"
        )
        assert ComparisonChecker.check(xml_bad_mm) is False

        # Unparseable non-int string returns False
        xml_bad_str = (
            "<Item returnType='boolean' key='Greater'>"
            "<Param key='#Left#'><Item key='LowestInRange' returnType='price'>"
            "<Param key='#TimeTo#'>invalid_time</Param></Item></Param>"
            "<Param key='#Right#'><Item key='Close' returnType='price'/></Param>"
            "</Item>"
        )
        assert ComparisonChecker.check(xml_bad_str) is False

    def test_bad_time_range_edge_cases(self) -> None:
        """Assert check_bad_time_range edge cases."""
        # Missing Param child in Number block
        num_no_param = ET.Element("Item", {"key": "Number"})
        bar_elem = ET.Element("Item", {"key": "BarHour"})
        assert ComparisonChecker.check_bad_time_range(bar_elem, num_no_param) is False

        # Unparseable float text in Param
        num_bad_text = ET.fromstring("<Item key='Number'><Param>abc</Param></Item>")
        assert ComparisonChecker.check_bad_time_range(bar_elem, num_bad_text) is False


class TestIndicatorFastSlowCheckerAST:
    """Test suite for IndicatorFastSlowChecker AST element verification."""

    def test_unparseable_element(self) -> None:
        """Assert unparseable element returns False."""
        assert IndicatorFastSlowChecker.check_block(None) is False
        assert IndicatorFastSlowChecker.check_block("<invalid xml") is False

    def test_fast_slow_direct_element(self) -> None:
        """Assert fast < slow is required on direct element."""
        # Fast < Slow passes
        xml_valid = (
            "<Item key='MACD'>"
            "<Param key='#FastPeriod#' type='int'>12</Param>"
            "<Param key='#SlowPeriod#' type='int'>26</Param>"
            "</Item>"
        )
        assert IndicatorFastSlowChecker.check(xml_valid) is True

        # Fast >= Slow fails
        xml_invalid = (
            "<Item key='MACD'>"
            "<Param key='#FastPeriod#' type='int'>26</Param>"
            "<Param key='#SlowPeriod#' type='int'>12</Param>"
            "</Item>"
        )
        assert IndicatorFastSlowChecker.check(xml_invalid) is False

        # Fast == Slow fails
        xml_equal = (
            "<Item key='MACD'>"
            "<Param key='#FastPeriod#' type='int'>20</Param>"
            "<Param key='#SlowPeriod#' type='int'>20</Param>"
            "</Item>"
        )
        assert IndicatorFastSlowChecker.check(xml_equal) is False

    def test_min_max_period(self) -> None:
        """Assert MinPeriod < MaxPeriod is required."""
        xml_valid = (
            "<Item key='Channel'>"
            "<Param key='#MinPeriod#' type='int'>5</Param>"
            "<Param key='#MaxPeriod#' type='int'>30</Param>"
            "</Item>"
        )
        assert IndicatorFastSlowChecker.check(xml_valid) is True

        xml_invalid = (
            "<Item key='Channel'>"
            "<Param key='#MinPeriod#' type='int'>50</Param>"
            "<Param key='#MaxPeriod#' type='int'>30</Param>"
            "</Item>"
        )
        assert IndicatorFastSlowChecker.check(xml_invalid) is False

    def test_nested_items_traversal(self) -> None:
        """Assert nested Item descendants are verified recursively."""
        xml_nested_valid = (
            "<Item key='Rule'>"
            "<Item key='MACD'>"
            "<Param key='#FastPeriod#' type='int'>10</Param>"
            "<Param key='#SlowPeriod#' type='int'>20</Param>"
            "</Item>"
            "</Item>"
        )
        assert IndicatorFastSlowChecker.check(xml_nested_valid) is True

        xml_nested_invalid = (
            "<Item key='Rule'>"
            "<Item key='MACD'>"
            "<Param key='#FastPeriod#' type='int'>30</Param>"
            "<Param key='#SlowPeriod#' type='int'>10</Param>"
            "</Item>"
            "</Item>"
        )
        assert IndicatorFastSlowChecker.check(xml_nested_invalid) is False

    def test_non_integer_periods_ignored(self) -> None:
        """Assert non-integer period values do not crash and return True."""
        xml_non_int = (
            "<Item key='MACD'>"
            "<Param key='#FastPeriod#' type='int'>abc</Param>"
            "<Param key='#SlowPeriod#' type='int'>def</Param>"
            "</Item>"
        )
        assert IndicatorFastSlowChecker.check(xml_non_int) is True


class TestPropertyCheckerAST:
    """Test suite for PropertyChecker AST element verification."""

    def test_unparseable_element(self) -> None:
        """Assert unparseable element returns False."""
        assert PropertyChecker.check_block(None) is False
        assert PropertyChecker.check_block("<bad xml") is False

    def test_non_boolean_skipped(self) -> None:
        """Assert non-boolean returnType is skipped (returns True)."""
        xml = "<Item returnType='number' key='IsRising'/>"
        assert PropertyChecker.check(xml) is True

    def test_non_rising_falling_skipped(self) -> None:
        """Assert non-IsRising/IsFalling key is skipped (returns True)."""
        xml = "<Item returnType='boolean' key='CrossesAbove'/>"
        assert PropertyChecker.check(xml) is True

    def test_missing_indicator_param_skipped(self) -> None:
        """Assert missing Indicator parameter is skipped (returns True)."""
        xml = "<Item returnType='boolean' key='IsRising'/>"
        assert PropertyChecker.check(xml) is True

    def test_indicator_without_shift_fails(self) -> None:
        """Assert indicator missing Shift parameter fails."""
        xml = (
            "<Item returnType='boolean' key='IsRising'>"
            "<Param key='#Indicator#'><Item key='SMA'><Param key='#Period#'>14</Param></Item></Param>"
            "</Item>"
        )
        assert PropertyChecker.check(xml) is False

    def test_indicator_with_time_blocks_fails(self) -> None:
        """Assert indicator using Hour, Minute, or DayOfWeek fails."""
        xml_hour = (
            "<Item returnType='boolean' key='IsFalling'>"
            "<Param key='#Indicator#'><Item key='SMA'>"
            "<Param key='#Shift#'>1</Param><Param key='#Hour#'>10</Param>"
            "</Item></Param>"
            "</Item>"
        )
        assert PropertyChecker.check(xml_hour) is False

        xml_minute = (
            "<Item returnType='boolean' key='IsRising'>"
            "<Param key='#Indicator#'><Item key='SMA'>"
            "<Param key='#Shift#'>1</Param><Param key='#Minute#'>30</Param>"
            "</Item></Param>"
            "</Item>"
        )
        assert PropertyChecker.check(xml_minute) is False

        xml_dow = (
            "<Item returnType='boolean' key='IsRising'>"
            "<Param key='#Indicator#'><Item key='SMA'>"
            "<Param key='#Shift#'>1</Param><Param key='#DayOfWeek#'>2</Param>"
            "</Item></Param>"
            "</Item>"
        )
        assert PropertyChecker.check(xml_dow) is False

    def test_valid_indicator_passes(self) -> None:
        """Assert indicator with Shift and no time parameters passes."""
        xml_valid = (
            "<Item returnType='boolean' key='IsRising'>"
            "<Param key='#Indicator#'><Item key='SMA'>"
            "<Param key='#Period#'>14</Param><Param key='#Shift#'>1</Param>"
            "</Item></Param>"
            "</Item>"
        )
        assert PropertyChecker.check(xml_valid) is True
