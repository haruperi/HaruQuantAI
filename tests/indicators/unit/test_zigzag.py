"""Causal ZigZag indicator tests."""

import pandas as pd
from app.services.indicators import zigzag

from tests.indicators.helpers import build_dataset, unwrap_response


def _dataset():
    """Build alternating confirmed high/low pivot evidence."""
    return build_dataset(
        [
            (5, 6, 4, 5, 10),
            (6, 8, 5, 7, 10),
            (8, 12, 7, 10, 10),
            (7, 9, 5, 6, 10),
            (5, 7, 2, 3, 10),
            (7, 10, 4, 9, 10),
            (10, 14, 8, 13, 10),
            (8, 11, 6, 7, 10),
            (6, 8, 1, 2, 10),
            (8, 11, 5, 10, 10),
            (11, 15, 9, 14, 10),
            (9, 12, 7, 8, 10),
            (7, 9, 3, 4, 10),
        ]
    )


def test_zigzag_emits_alternating_pivots_on_confirmation_rows() -> None:
    """Confirmed outputs alternate and use their confirmation timestamps."""
    data = _dataset()
    result = unwrap_response(zigzag(data, depth=2))
    ready = result.values_only.dropna(subset=["zigzag_value_2"])
    assert ready["zigzag_type_2"].tolist() == [1.0, -1.0, 1.0, -1.0, 1.0]
    assert ready["zigzag_value_2"].tolist() == [12.0, 2.0, 14.0, 1.0, 15.0]
    assert all(ready["available_at"] >= ready.index)


def test_zigzag_prefix_is_not_revised_by_later_bars() -> None:
    """Adding later bars does not alter any previously emitted pivot."""
    data = _dataset()
    prefix = data.model_copy(
        update={
            "records": data.records[:9],
            "end": data.records[8].timestamp,
            "available_at": data.records[8].available_at,
            "record_count": 9,
            "quality_report": data.quality_report.model_copy(
                update={"record_count": 9, "checked_count": 9}
            ),
        }
    )
    prefix_result = unwrap_response(zigzag(prefix, depth=2))
    full_result = unwrap_response(zigzag(data, depth=2))
    pd.testing.assert_frame_equal(
        prefix_result.values_only,
        full_result.values_only.iloc[:9],
    )
