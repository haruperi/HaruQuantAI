"""Unit tests for app/services/data/evidence/account_state.py to reach >80% coverage."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.services.data.contracts import DataError
from app.services.data.evidence.account_contracts import AccountSnapshotRequest
from app.services.data.evidence.account_state import (
    _map_orders,
    _map_positions,
    _required_decimal,
    _validate_freshness,
    get_account_state_snapshot,
)

_REQ_ID = "req-11111111-1111-4111-8111-111111111111"
_NOW = datetime.now(UTC)


def test_required_decimal_non_finite() -> None:
    """Test _required_decimal raises STALE_EVIDENCE for None or non-finite Decimal."""
    with pytest.raises(DataError) as exc_info:
        _required_decimal(None, field="test_field", request_id=_REQ_ID)
    assert exc_info.value.code == "STALE_EVIDENCE"

    with pytest.raises(DataError) as exc_info:
        _required_decimal(Decimal("NaN"), field="test_field", request_id=_REQ_ID)
    assert exc_info.value.code == "STALE_EVIDENCE"


def test_map_positions_invalid_side() -> None:
    """Test _map_positions raises STALE_EVIDENCE for invalid side."""
    mock_pos = MagicMock()
    mock_pos.side = "INVALID_SIDE"
    with pytest.raises(DataError) as exc_info:
        _map_positions((mock_pos,), _REQ_ID)
    assert exc_info.value.code == "STALE_EVIDENCE"


def test_map_orders_invalid_side() -> None:
    """Test _map_orders raises STALE_EVIDENCE for invalid side."""
    mock_order = MagicMock()
    mock_order.side = "INVALID_SIDE"
    with pytest.raises(DataError) as exc_info:
        _map_orders((mock_order,), _REQ_ID)
    assert exc_info.value.code == "STALE_EVIDENCE"


def test_validate_freshness_stale_or_future() -> None:
    """Test _validate_freshness raises STALE_EVIDENCE for stale or future timestamp."""
    # Stale timestamp
    retrieved_old = _NOW - timedelta(seconds=100)
    with pytest.raises(DataError) as exc_info:
        _validate_freshness(_NOW, retrieved_old, max_age_seconds=10, request_id=_REQ_ID)
    assert exc_info.value.code == "STALE_EVIDENCE"

    # Future timestamp
    retrieved_future = _NOW + timedelta(seconds=100)
    with pytest.raises(DataError) as exc_info:
        _validate_freshness(
            _NOW, retrieved_future, max_age_seconds=10, request_id=_REQ_ID
        )
    assert exc_info.value.code == "STALE_EVIDENCE"


def test_get_account_state_snapshot_mismatched_account_id() -> None:
    """
    Test get_account_state_snapshot surfaces STALE_EVIDENCE for mismatched account_id.
    """
    req = AccountSnapshotRequest(
        source_id="mt5",
        account_id="ACC_123",
        max_age_seconds=30,
        request_id=_REQ_ID,
    )
    mock_adapter = MagicMock()
    info_res = MagicMock()
    info_res.error = None
    info_res.data.account_id = "ACC_DIFFERENT"
    info_res.data.currency = "USD"
    info_res.data.retrieved_at = _NOW
    info_res.data.equity = Decimal(10000)

    mock_adapter.get_account_info = AsyncMock(return_value=info_res)
    mock_adapter.get_balances = AsyncMock(return_value=MagicMock(error=None, data=()))
    mock_adapter.get_positions = AsyncMock(
        return_value=MagicMock(error=None, data=MagicMock(truncated=False, items=()))
    )
    mock_adapter.get_orders = AsyncMock(
        return_value=MagicMock(error=None, data=MagicMock(truncated=False, items=()))
    )
    mock_adapter.get_permissions = AsyncMock(
        return_value=MagicMock(error=None, data=MagicMock(trade_write=True))
    )
    mock_adapter.is_connected = AsyncMock(return_value=MagicMock(error=None, data=True))

    response = get_account_state_snapshot(req, mock_adapter)
    assert response.status != "success"
    assert response.error is not None
    assert response.error.code == "STALE_EVIDENCE"
