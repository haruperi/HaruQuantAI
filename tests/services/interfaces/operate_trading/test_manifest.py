"""Unit tests for the operate-trading manifest."""

from app.contracts.interfaces.capabilities import OPERATE_TRADING_CAPABILITY
from app.contracts.trading.capabilities import (
    ACCOUNT_OPERATIONS_CAPABILITY,
    DISPATCH_ORDERS_CAPABILITY,
    MANAGE_TRADING_SESSIONS_CAPABILITY,
)
from app.services.interfaces.operate_trading.manifest import SPEC


def test_manifest_spec() -> None:
    """Verify feature specification constants and declarations."""
    assert SPEC.feature_id == "FEAT-IFACE-OPERATE_TRADING"
    assert SPEC.domain == "interfaces"
    assert SPEC.provides == frozenset({OPERATE_TRADING_CAPABILITY})
    assert SPEC.requires == frozenset()
    assert SPEC.optional == frozenset(
        {
            ACCOUNT_OPERATIONS_CAPABILITY,
            DISPATCH_ORDERS_CAPABILITY,
            MANAGE_TRADING_SESSIONS_CAPABILITY,
        }
    )
    assert SPEC.conflicts == frozenset()
    assert SPEC.state is None
    assert SPEC.config_keys == frozenset({"default_account_id", "max_order_quantity"})
    SPEC.validate()


def test_manifest_capability_identifiers() -> None:
    """Verify the provided capability identifier."""
    (provided,) = SPEC.provides
    assert provided.identifier == "interfaces.operate-trading@1"
