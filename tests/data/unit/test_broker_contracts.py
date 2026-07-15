"""Unit tests for read-only account evidence."""

from decimal import Decimal

import pytest
from app.services.data.contracts import AccountStateSnapshot
from app.services.data.contracts.errors import DataError

from tests.data.helpers import START


def test_account_snapshot_rejects_stale_evidence() -> None:
    """A snapshot expiry must be strictly later than its evidence time."""
    with pytest.raises(DataError):
        AccountStateSnapshot(
            account_id="acct-1",
            currency="USD",
            balances=(),
            equity=Decimal(0),
            positions=(),
            orders=(),
            connected=False,
            trading_allowed=False,
            source_id="broker",
            snapshot_at=START,
            expires_at=START,
            request_id="req-dd37fc1c2cd6d665f9a7a7f9a2482efe3347c7bb51ac073ef12ef9b7eb511055",
        )
