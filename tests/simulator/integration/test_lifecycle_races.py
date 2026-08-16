"""Integration evidence for lifecycle partial-order race records."""

from datetime import UTC, datetime, timedelta

from app.services.simulator.execution.lifecycle import describe_lifecycle_race


def test_ambiguous_concurrent_authority_order_is_not_invented() -> None:
    """All named race classes preserve evidence without invented sequence."""
    now = datetime(2026, 8, 17, tzinfo=UTC)
    for left, right in (
        ("cancel", "fill"),
        ("modify", "fill"),
        ("protection", "close"),
        ("disconnect", "response"),
    ):
        concurrent = describe_lifecycle_race(
            left_event_id=left,
            right_event_id=right,
            left_at=now,
            right_at=now,
            evidenced_predecessor=None,
        )
        assert concurrent["relation"] == "CONCURRENT"
        assert concurrent["provider_sequence_claimed"] is False
        ordered = describe_lifecycle_race(
            left_event_id=left,
            right_event_id=right,
            left_at=now,
            right_at=now + timedelta(microseconds=1),
            evidenced_predecessor=left,
        )
        assert ordered["relation"] == "LEFT_BEFORE_RIGHT"
        assert ordered["provider_sequence_claimed"] is True
