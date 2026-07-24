"""Critical operational alert delivery tests."""

from app.services.api import (
    build_kill_switch_activation_alert,
    deliver_critical_alert,
)

from tests.risk import _support as risk_support


def test_delivery_attempts_sink_exactly_once() -> None:
    """Verify successful delivery uses deterministic idempotency exactly once."""
    alert = build_kill_switch_activation_alert(
        risk_support._inactive_state().model_copy(update={"state": "active"}),
        risk_support._auth(risk_support._config()),
    )
    calls: list[str] = []

    def sink(value: object, *, idempotency_key: str) -> None:
        """Record one delivery call."""
        del value
        calls.append(idempotency_key)

    result = deliver_critical_alert(alert, sink)

    assert result.status == "delivered"
    assert result.failure_code is None
    assert calls == [alert.alert_id]


def test_delivery_failure_is_visible_and_non_authoritative() -> None:
    """Verify a sink failure is one attempt and cannot alter source truth."""
    state = risk_support._inactive_state().model_copy(update={"state": "active"})
    alert = build_kill_switch_activation_alert(
        state,
        risk_support._auth(risk_support._config()),
    )
    calls = 0

    def sink(value: object, *, idempotency_key: str) -> None:
        """Reject one delivery call."""
        nonlocal calls
        del value, idempotency_key
        calls += 1
        raise RuntimeError("test sink unavailable")

    result = deliver_critical_alert(alert, sink)

    assert result.status == "failed"
    assert result.failure_code == "ALERT_DELIVERY_FAILED"
    assert calls == 1
    assert state.state == "active"
