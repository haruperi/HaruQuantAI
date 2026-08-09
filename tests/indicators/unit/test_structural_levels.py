from datetime import UTC, datetime, timedelta

from app.services.indicators import project_structural_levels


def test_structural_levels_reject_future_observations() -> None:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    result = project_structural_levels(
        [
            {
                "kind": "support",
                "price": 99.0,
                "observed_at": now - timedelta(minutes=1),
                "invalidation_price": 98.0,
            }
        ],
        decision_time=now,
    )
    assert result.data[0]["kind"] == "support"


def test_structural_levels_reject_malformed_evidence() -> None:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    assert (
        project_structural_levels([], decision_time=now.replace(tzinfo=None)).status
        == "error"
    )
    assert project_structural_levels([{}], decision_time=now).status == "error"
    malformed = {
        "kind": "",
        "price": 1.0,
        "observed_at": now,
        "invalidation_price": 2.0,
    }
    assert project_structural_levels([malformed], decision_time=now).status == "error"
    assert (
        project_structural_levels(
            [dict(malformed, kind="support", observed_at=now.replace(tzinfo=None))],
            decision_time=now,
        ).status
        == "error"
    )
    assert (
        project_structural_levels(
            [dict(malformed, kind="support", price=float("nan"))], decision_time=now
        ).status
        == "error"
    )
