"""Unit tests for ComposerSelection (PC-002)."""

from __future__ import annotations

import re

import pytest
from app.workspace.portfolio_composer.selection import ComposerSelection


class TestComposerSelection:
    """Test suite for ComposerSelection parsing and decimal precision."""

    @pytest.mark.parametrize(
        ("value", "expected_member", "expected_decimals"),
        [
            ("SharpRatio", ComposerSelection.SHARPE, 3),
            ("ReturnDrawdownRatio", ComposerSelection.RETURN_DRAWDOWN, 0),
            ("CAGRMaxDrawdownRatio", ComposerSelection.CAGR_MAX_DRAWDOWN, 2),
            ("CAGRMeanDrawdownRatio", ComposerSelection.CAGR_MEAN_DRAWDOWN, 2),
            ("NetProfit", ComposerSelection.NET_PROFIT, 0),
        ],
    )
    def test_parse_valid_and_decimals(
        self,
        value: str,
        expected_member: ComposerSelection,
        expected_decimals: int,
    ) -> None:
        """Verify all five accepted selection strings parse correctly."""
        parsed = ComposerSelection.parse(value)
        assert parsed is expected_member
        assert parsed.value == value
        assert parsed.decimals() == expected_decimals

    @pytest.mark.parametrize(
        "invalid_value",
        [
            "SharpeRatio",
            "sharpratio",
            "SHARPRATIO",
            "",
            "   ",
            "netprofit",
            "unknown",
        ],
    )
    def test_invalid_strings_raise_exact_value_error(self, invalid_value: str) -> None:
        """Verify inexact or misspelt strings raise exact ValueError."""
        pattern = rf"^Invalid PortfolioSelectionType: {re.escape(invalid_value)}$"
        with pytest.raises(ValueError, match=pattern):
            ComposerSelection.parse(invalid_value)

    @pytest.mark.parametrize("invalid_arg", [None, 1, 3.14, True, False, [], {}])
    def test_non_string_raises_type_error(self, invalid_arg: object) -> None:
        """Verify non-string arguments raise exact TypeError."""
        with pytest.raises(TypeError, match=r"^selection_type must be a string$"):
            ComposerSelection.parse(invalid_arg)  # type: ignore[arg-type]
