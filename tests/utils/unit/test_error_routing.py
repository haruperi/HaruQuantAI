from collections.abc import Mapping

import pytest
from app.utils import ValidationError, route_error_event


def test_route_error_event_invokes_injected_sink() -> None:
    events: list[Mapping[str, str]] = []
    payload = route_error_event(
        ValidationError("VALIDATION_FAILED", "FIELD_MISSING"),
        events.append,
    )
    assert events == [payload]
    assert payload == {"code": "VALIDATION_FAILED", "detail": "FIELD_MISSING"}


def test_route_error_event_propagates_sink_failure() -> None:
    def failing_sink(_payload: Mapping[str, str]) -> None:
        raise RuntimeError("sink unavailable")

    with pytest.raises(RuntimeError, match="sink unavailable"):
        route_error_event(ValidationError("VALIDATION_FAILED"), failing_sink)
