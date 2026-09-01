"""Shared initial Trading/Simulation authority-state identity evidence."""

from decimal import Decimal

import pytest
from app.kernel.serialization import canonical_digest
from app.services.simulator.errors import SimulationError
from app.services.simulator.state.runtime import validate_initial_authority_state


def _snapshot() -> dict[str, object]:
    """Return one complete empty-account authority snapshot."""
    return {
        "account": {"balance": Decimal(10000), "currency": "USD"},
        "orders": (),
        "positions": (),
        "deals": (),
        "ownership": {"mode": "exclusive"},
    }


def test_initial_authority_hash_binds_both_routes() -> None:
    """The exact request-bound snapshot is returned without reconstruction."""
    snapshot = _snapshot()
    validated = validate_initial_authority_state(
        snapshot,
        expected_hash=canonical_digest(snapshot),
        account_currency="USD",
        initial_balance=Decimal(10000),
    )
    assert validated is snapshot


@pytest.mark.parametrize("mutation", ["hash", "balance", "missing"])
def test_incomplete_or_different_initial_state_fails_closed(mutation: str) -> None:
    """Hash, account, and completeness disagreement cannot start a run."""
    snapshot = _snapshot()
    expected = canonical_digest(snapshot)
    if mutation == "hash":
        expected = "0" * 64
    elif mutation == "balance":
        snapshot["account"] = {"balance": Decimal(9999), "currency": "USD"}
        expected = canonical_digest(snapshot)
    else:
        del snapshot["deals"]
        expected = canonical_digest(snapshot)
    with pytest.raises(SimulationError):
        validate_initial_authority_state(
            snapshot,
            expected_hash=expected,
            account_currency="USD",
            initial_balance=Decimal(10000),
        )
