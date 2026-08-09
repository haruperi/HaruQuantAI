"""Unit tests for append-only audit sink routing."""

import pytest
from app.utils import route_audit_event


def test_sink_failure_is_surfaced_not_swallowed() -> None:
    def failing_sink(event: object) -> None:
        raise RuntimeError("sink failed")

    with pytest.raises(RuntimeError, match="sink failed"):
        route_audit_event(
            {"contract_version": "v1", "schema_id": "utils.event_envelope.v1"},
            failing_sink,
        )
