"""Unit tests for availability, schedule, and volume contracts."""

import pytest
from app.services.data.contracts import AvailabilityRequest, VolumeRequest, VolumeResult
from app.services.data.contracts.errors import DataError

from tests.data.helpers import END, START


def test_reference_contracts_require_bounds_and_units() -> None:
    """Reference requests and results keep explicit positive bounds and units."""
    with pytest.raises(DataError):
        AvailabilityRequest(
            source_id="fixture",
            symbol="ABC",
            data_kind="tick",
            max_probe_records=0,
            request_id="req-39b6a33ddd7c2e35300b6d1e594b85314d2143f2b8f4b574648e1e8086ac4517",
        )
    with pytest.raises(DataError):
        VolumeRequest(
            source_id="fixture",
            symbol="ABC",
            start=START,
            end=END,
            mode="buckets",
            limit=10,
            request_id="req-c9e591850b4b55da1d369e4504db757eadffabdbbc54ab48bf37dae5b3c4a3a4",
        )
    with pytest.raises(DataError):
        VolumeResult(
            source_id="fixture",
            symbol="ABC",
            mode="records",
            volume_kind="trade",
            volume_unit="",
            records=(),
            provenance={"source": "fixture"},
            truncated=False,
            request_id="req-36c19ee390ab3880f7225e4f38e30d3635d2ab545b58bba5c6bc371ca519ce4b",
        )
