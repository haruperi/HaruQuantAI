from datetime import UTC, datetime

from app.services.indicators import build_chart_pattern_evidence


def test_chart_pattern_evidence_never_authorizes_trade() -> None:
    result = build_chart_pattern_evidence(
        {"doji": 1, "engulfing": -1},
        observed_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    assert result.data["authorizes_trade"] is False
