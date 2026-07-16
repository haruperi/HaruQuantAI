"""Unit tests for bounded feed contracts."""

import pytest
from app.services.data.contracts import FeedEventResult, FeedStatus, RawFeedEvent
from app.services.data.contracts.errors import DataError

from tests.data.helpers import AVAILABLE, START


def test_feed_contracts_are_bounded_and_status_is_evidence_based() -> None:
    """Drops require gaps and running feeds require heartbeat evidence."""
    with pytest.raises(DataError):
        FeedEventResult(
            feed_id="feed-1",
            sequence=1,
            accepted=False,
            buffer_depth=0,
            gap_recorded=False,
            dropped_count=1,
            request_id="req-70280872bba6fdeb1b2789e6d6bbff0b2ec16fb7166e1bea9767d5e9b132df50",
        )
    with pytest.raises(DataError):
        FeedStatus(
            feed_id="feed-1",
            source_id="fixture",
            symbol="ABC",
            data_kind="tick",
            state="running",
            buffer_depth=0,
            buffer_capacity=10,
            dropped_count=0,
            gap_count=0,
            reconnect_count=0,
            breaker_state="closed",
            request_id="req-19008909f52936622bcbb72143057f7a79cafe14ce1a6e1ba01773238698abf5",
        )
    with pytest.raises(DataError):
        RawFeedEvent(
            feed_id="feed-1",
            sequence=1,
            event_timestamp=AVAILABLE,
            received_at=START,
            payload={"bid": "10"},
            request_id="req-77203a0660ef954a16e8dd20f946ffaf6e077f714064f4ce3780500f45b2e566",
        )
