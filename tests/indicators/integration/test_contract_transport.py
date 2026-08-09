import json
from datetime import UTC, datetime

from app.services.indicators import build_liquidity_snapshot


def test_versioned_contract_transport_is_json_safe() -> None:
    result = build_liquidity_snapshot(
        observed_at=datetime(2026, 1, 1, tzinfo=UTC),
        spread=0.1,
        executable_depth=1.0,
        imbalance=0.0,
        volume=1.0,
        fill_probability=None,
        regime="UNKNOWN",
        complete=False,
    )
    assert json.loads(json.dumps(result.data)) == result.data
