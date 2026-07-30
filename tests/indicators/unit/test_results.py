"""Public Indicators result-boundary tests."""

from app.services.indicators import (
    get_indicator_result_metadata,
    get_indicator_result_values,
    join_indicator_result,
    sma,
)

from tests.indicators.helpers import build_dataset, unwrap_response


def _result():
    """Calculate one result through the documented package-root API."""
    return unwrap_response(sma(build_dataset([(1, 2, 0, 1, 10)] * 4), period=2))


def test_result_metadata_is_detached_and_complete() -> None:
    """FR-INDI-007/008: metadata exposes stable identity without classes."""
    metadata = get_indicator_result_metadata(_result())
    assert metadata["schema_id"] == "indicators.indicator_series.v1"
    assert metadata["indicator_id"] == "sma"
    assert metadata["manifest"]["output_checksum"]


def test_values_projection_is_copy_safe() -> None:
    """FR-INDI-009: values are returned as a detached projection."""
    result = _result()
    first = get_indicator_result_values(result)
    first.loc[:, "sma_2"] = 999.0
    second = get_indicator_result_values(result)
    assert second["sma_2"].iloc[-1] != 999.0
    assert "open" not in second.columns


def test_join_preserves_dataset_and_alignment() -> None:
    """FR-INDI-010: joining uses the public function-only boundary."""
    dataset = build_dataset([(1, 2, 0, 1, 10)] * 4)
    result = unwrap_response(sma(dataset, period=2))
    joined = unwrap_response(join_indicator_result(result, dataset))
    assert "close" in joined.columns
    assert "sma_2" in joined.columns
    assert len(joined) == dataset.record_count


def test_join_rejects_a_different_dataset() -> None:
    """The public join operation fails closed for mismatched source evidence."""
    dataset = build_dataset([(1, 2, 0, 1, 10)] * 4)
    result = unwrap_response(sma(dataset, period=2))
    other = build_dataset([(2, 3, 1, 2, 10)] * 4)
    response = join_indicator_result(result, other)
    assert response.status == "error"
    assert response.error is not None
    assert response.error.code == "IND_INPUT_MUTATION_DETECTED"
