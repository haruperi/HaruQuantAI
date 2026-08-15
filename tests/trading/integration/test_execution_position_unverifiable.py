"""Integration evidence for fail-closed unverifiable execution positions."""

import pytest
from app.services.trading import (
    create_execution_position_store,
    get_execution_position,
    reconcile_execution_position_receipt,
)

from tests.trading.unit.state.test_execution_position_correlation import (
    _Adapter,
    _receipt,
)


@pytest.mark.anyio
async def test_fr_trd_086_missing_deal_identity_becomes_unknown() -> None:
    """FR-TRD-086: missing deal authority blocks the affected position scope."""
    state = await reconcile_execution_position_receipt(
        _receipt(deals=()),
        create_execution_position_store(),
        _Adapter(),
        account_id="account-1",
        symbol="EURUSD",
    )
    assert state.state == "UNKNOWN"
    assert state.unknown_reason == "receipt has no provider deal identity"


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("adapter", "reason"),
    [
        (_Adapter(source_sequence=None), "incomplete or disagrees"),
        (_Adapter(position_symbol="GBPUSD"), "incomplete or disagrees"),
    ],
)
async def test_authority_gap_or_snapshot_disagreement_blocks_target(
    adapter: _Adapter, reason: str
) -> None:
    """Missing sequence and snapshot disagreement mark the correlated ID UNKNOWN."""
    store = create_execution_position_store()
    state = await reconcile_execution_position_receipt(
        _receipt("receipt-gap", ("deal-gap",)),
        store,
        adapter,
        account_id="account-1",
        symbol="EURUSD",
    )
    assert state.state == "UNKNOWN"
    assert reason in state.unknown_reason
    assert get_execution_position(store, "broker-position-1") is state


@pytest.mark.anyio
async def test_unknown_deal_blocks_without_requesting_position() -> None:
    """An unknown provider deal never permits a position-authority guess."""
    state = await reconcile_execution_position_receipt(
        _receipt("receipt-unknown-deal", ("deal-unknown",)),
        create_execution_position_store(),
        _Adapter(deal_available=False),
        account_id="account-1",
        symbol="EURUSD",
    )
    assert state.state == "UNKNOWN"
    assert state.unknown_reason == "provider deal cannot be verified"


@pytest.mark.anyio
async def test_late_receipt_with_regressed_authority_sequence_blocks() -> None:
    """Late authority evidence cannot roll a position projection backward."""
    store = create_execution_position_store()
    await reconcile_execution_position_receipt(
        _receipt("receipt-new", ("deal-new",)),
        store,
        _Adapter(source_sequence=9),
        account_id="account-1",
        symbol="EURUSD",
    )
    late = await reconcile_execution_position_receipt(
        _receipt("receipt-late", ("deal-late",)),
        store,
        _Adapter(source_sequence=8),
        account_id="account-1",
        symbol="EURUSD",
    )
    assert late.state == "UNKNOWN"
    assert late.unknown_reason == "position authority sequence regressed"
