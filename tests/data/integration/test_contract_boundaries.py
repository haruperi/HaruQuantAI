"""Integration tests for Data contract ownership boundaries."""

from decimal import Decimal

from app.services.data import (
    __all__ as data_public_api,
)
from app.services.data import (
    build_account_state_snapshot,
    build_audit_event_page,
)
from app.utils.contracts.audit import AuditEvent

from tests.data.helpers import END, START, make_audit_event


def test_data_contracts_exclude_provider_runtime_types() -> None:
    """Broker evidence is normalized without adapter or provider objects."""
    snapshot = build_account_state_snapshot(
        account_id="acct-1",
        currency="USD",
        balances=(),
        equity=Decimal(0),
        positions=(),
        orders=(),
        connected=True,
        trading_allowed=False,
        source_id="broker-a",
        snapshot_at=START,
        expires_at=END,
        request_id="req-1a2a3f3a665ae6ac4cbba2feb661f5a87257b8e9f53f1853588d1842360cd209",
    )
    assert snapshot.account_id == "acct-1"
    assert "BrokerAdapter" not in repr(snapshot)
    assert "Provider" not in repr(snapshot)
    assert len(data_public_api) == len(set(data_public_api))
    assert "get_account_state_snapshot" in data_public_api
    assert "get_market_data" in data_public_api
    assert "to_ohlcv_dataframe" in data_public_api
    assert "to_tick_dataframe" in data_public_api


def test_audit_page_uses_utils_owned_event_contract() -> None:
    """Data persists and pages the Utils-owned canonical audit envelope."""
    event = make_audit_event()
    page = build_audit_event_page(
        events=(event,),
        request_id="req-b9079292e61f241af2fb05632499fcedb66c43bcadbe960298162cc15ce13532",
    )
    assert isinstance(page.events[0], AuditEvent)
