"""WF-INDI-002 integration tests for decision-time indicator evidence."""

from datetime import timedelta

from app.services.indicators import ema, get_indicator_result_values

from tests.indicators.helpers import close_dataset, unwrap_response


def test_indicator_series_is_availability_qualified_at_decision_time() -> None:
    """WF-INDI-002: every exposed EMA row carries causal availability."""
    data = close_dataset([1.0, 2.0, 3.0, 4.0, 5.0])
    result = unwrap_response(ema(data, period=2))
    values = get_indicator_result_values(result)
    decision_time = data.available_at + timedelta(seconds=1)

    qualified = values.loc[values["available_at"] <= decision_time]

    assert len(qualified) == data.record_count
    assert qualified["ema_2"].iloc[-1] == 4.5
    assert qualified["available_at"].is_monotonic_increasing
