"""Unit tests for HealthState v1."""

from app.utils import build_health_state


def test_absent_observation_yields_unknown() -> None:
    result = build_health_state(
        dependency="broker",
        category="TRANSIENT",
        state="DEGRADED",
        retryable=True,
        operator_action="Inspect",
        observed_at=None,
    )
    assert result["state"] == "UNKNOWN"
    assert result["retryable"] is False
