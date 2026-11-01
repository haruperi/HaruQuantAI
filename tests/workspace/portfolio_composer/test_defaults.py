"""Unit tests for ComposerDefaults (PC-001)."""

from __future__ import annotations

import pytest
from app.workspace.portfolio_composer.defaults import ComposerDefaults


class TestComposerDefaults:
    """Test suite for ComposerDefaults creation and immutability/freshness."""

    def test_exact_defaults(self) -> None:
        """Verify the exact dictionary produced by ComposerDefaults."""
        result = ComposerDefaults.create(today_label="injected-day")
        expected = {
            "date_range": "full",
            "start_day": "injected-day",
            "end_day": "injected-day",
            "initial_capital": 100000,
            "leverage": 1,
            "results": [],
            "weights": [],
            "mm_methods": [],
            "mm_methods_different": False,
            "portfolio_name": None,
            "model_type": "markowitz",
            "selection_type": "SharpRatio",
            "max_simulations": 10,
            "conf_level": 95,
            "risk_free_rate": 0.7,
            "req_std_dev": -1,
        }
        assert result == expected

    def test_fresh_lists(self) -> None:
        """Verify mutable collections are fresh instances on every call."""
        d1 = ComposerDefaults.create(today_label="day-1")
        d2 = ComposerDefaults.create(today_label="day-2")

        # Distinct identities across instances
        assert d1["results"] is not d2["results"]
        assert d1["weights"] is not d2["weights"]
        assert d1["mm_methods"] is not d2["mm_methods"]

        # Distinct identities within the same dictionary
        assert d1["results"] is not d1["weights"]
        assert d1["results"] is not d1["mm_methods"]
        assert d1["weights"] is not d1["mm_methods"]

        # Mutating d1 does not pollute d2
        d1["results"].append("strategy-1")
        assert d2["results"] == []
        assert d2["weights"] == []
        assert d2["mm_methods"] == []

    @pytest.mark.parametrize(
        "invalid_arg",
        [None, 123, 45.6, True, ["2026-01-01"], {"day": "2026"}],
    )
    def test_invalid_type_raises(self, invalid_arg: object) -> None:
        """Verify non-str arguments raise exact TypeError."""
        with pytest.raises(TypeError, match=r"^today_label must be a string$"):
            ComposerDefaults.create(today_label=invalid_arg)  # type: ignore[arg-type]
