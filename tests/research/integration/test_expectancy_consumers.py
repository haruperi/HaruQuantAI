"""Cross-domain provider evidence for FEAT-RES-14."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.services.research import (
    build_expectancy_profile,
    build_risk_expectancy_provider,
    build_strategy_expectancy_provider,
    transition_expectancy_governance,
)
from app.services.risk import evaluate_reward_risk_gate
from app.services.strategy import (
    build_expectancy_reference,
    evaluate_expectancy_reference,
)


def _approved() -> dict[str, object]:
    """Build a bounded approved provider fixture."""
    now = datetime(2026, 1, 1, tzinfo=UTC)
    profile = build_expectancy_profile(
        exact_version="1",
        hypothesis="edge",
        strategy_ref="strategy-demo",
        instruments=("EURUSD",),
        regimes=("trend",),
        sessions=("london",),
        sample_from_utc=now - timedelta(days=30),
        sample_to_utc=now - timedelta(days=1),
        sample_size=100,
        out_of_sample_status="walk_forward",
        win_rate=0.6,
        avg_win_r=2.0,
        avg_loss_r=1.0,
        expected_value_r=0.8,
        max_drawdown_r=4.0,
        min_reward_risk=1.5,
        evidence_ref="artifact-demo",
    )
    for state in ("under_review", "approved"):
        profile = transition_expectancy_governance(
            profile,
            target_state=state,
            reviewer="reviewer",
            decision=state,
            reason="EVIDENCE_ACCEPTED",
            now_utc=now,
        )
    return profile


def test_strategy_and_risk_consume_research_adapters() -> None:
    """FR-RES-111: exact Strategy and Risk ports consume Research evidence."""
    profile = _approved()

    def now() -> datetime:
        """Return the deterministic provider evaluation instant."""
        return datetime(2026, 1, 2, tzinfo=UTC)

    strategy_provider = build_strategy_expectancy_provider(
        profile_loader=lambda _profile_id: profile, now_provider=now
    )
    reference = build_expectancy_reference(
        profile_id=str(profile["profile_id"]),
        exact_version="1",
        evidence_ref="artifact-demo",
    )
    assert (
        evaluate_expectancy_reference(reference, provider=strategy_provider)
        == "ELIGIBLE"
    )
    risk_provider = build_risk_expectancy_provider(
        profile_loader=lambda _strategy_ref: profile, now_provider=now
    )
    result = evaluate_reward_risk_gate(
        "strategy-demo",
        Decimal("1.6"),
        Decimal("2.0"),
        ("artifact-demo",),
        expectancy_provider=risk_provider,
    )
    assert result.status == "success"
    assert result.data is not None
    assert str(result.data.status).lower().endswith("pass")
