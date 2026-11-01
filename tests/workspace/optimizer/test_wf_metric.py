"""Tests for first_wf_metric projection helper."""

import math

import pytest
from app.workspace.optimizer.wf_metric import first_wf_metric


class TestFirstWFMetric:
    """Test suite verifying first_wf_metric projection behavior and edge cases."""

    def test_none_and_empty_sequence(self) -> None:
        """Verify None and empty list both yield 0.0."""
        assert first_wf_metric(None, "NetProfit") == 0.0
        assert first_wf_metric([], "NetProfit") == 0.0

    def test_empty_first_element(self) -> None:
        """Verify [{}] yields 0.0."""
        assert first_wf_metric([{}], "NetProfit") == 0.0

    def test_first_element_extraction(self) -> None:
        """Verify metric is taken from the first record only, ignoring subsequent records."""
        data = [{"NetProfit": 12.5}, {"NetProfit": 99.0}]
        assert first_wf_metric(data, "NetProfit") == 12.5

    def test_missing_metric_in_first_element(self) -> None:
        """Verify missing metric defaults to 0.0 even if present in later records."""
        data = [{"Other": 1.0}, {"NetProfit": 99.0}]
        assert first_wf_metric(data, "NetProfit") == 0.0

    def test_negative_metric_preserved(self) -> None:
        """Verify negative metric values are preserved without clamping."""
        data = [{"NetProfit": -4.0}]
        assert first_wf_metric(data, "NetProfit") == -4.0

    def test_input_immutability(self) -> None:
        """Verify input dictionaries and sequences are not mutated."""
        item1 = {"NetProfit": 12.5}
        item2 = {"NetProfit": 99.0}
        data = [item1, item2]
        res = first_wf_metric(data, "NetProfit")
        assert res == 12.5
        assert item1 == {"NetProfit": 12.5}
        assert item2 == {"NetProfit": 99.0}
        assert len(data) == 2

    def test_invalid_metric_guards(self) -> None:
        """Verify non-empty string validation raises ValueError."""
        with pytest.raises(ValueError, match="metric must be non-empty"):
            first_wf_metric([{"NetProfit": 1.0}], "")

        with pytest.raises(ValueError, match="metric must be non-empty"):
            first_wf_metric([{"NetProfit": 1.0}], None)  # type: ignore[arg-type]

    def test_ieee_nan_and_infinity_preserved(self) -> None:
        """Verify IEEE NaN and inf are returned faithfully."""
        nan_res = first_wf_metric([{"Metric": float("nan")}], "Metric")
        assert math.isnan(nan_res)

        inf_res = first_wf_metric([{"Metric": float("inf")}], "Metric")
        assert math.isinf(inf_res)
        assert inf_res > 0
