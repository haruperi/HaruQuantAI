"""Unit tests for normalized Trading authority snapshots."""

# ruff: noqa: INP001

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.services.trading.reconciliation import AuthoritySnapshot
from app.utils import to_json_safe

NOW = datetime(2026, 7, 19, 8, 0, tzinfo=UTC)


def test_snapshot_is_json_safe() -> None:
    """Normalized authority evidence contains no provider-native objects."""
    snapshot = AuthoritySnapshot(
        route="paper",
        authority_id="mt5",
        account_id="account-001",
        source_id="broker-read-001",
        account={"equity": Decimal("10000.00")},
        orders={"order-001": {"quantity": Decimal("1.00")}},
        positions={"position-001": {"quantity": Decimal("1.00")}},
        observed_at=NOW,
        expires_at=NOW + timedelta(minutes=1),
    )
    safe = to_json_safe(snapshot.model_dump(mode="python"))
    assert isinstance(safe, dict)
    assert safe["orders"] == {"order-001": {"quantity": "1.00"}}
