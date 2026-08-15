"""Effective revision selection integration tests."""

from datetime import timedelta
from decimal import Decimal

from app.services.simulator import calculate_fx_profit, unwrap_simulation_response

from tests.simulator.unit.calculations.test_profit import NOW, revision


def test_unique_revision_is_selected_at_half_open_boundary() -> None:
    """The successor owns the exact prior effective-to instant."""
    first = revision(contract_size="100000")
    first["effective_to"] = (NOW + timedelta(hours=1)).isoformat()
    second = revision(contract_size="200000")
    second["revision_id"] = "revision-2"
    second["effective_from"] = first["effective_to"]
    revisions = {"complete_coverage": True, "revisions": (first, second)}
    result = unwrap_simulation_response(
        calculate_fx_profit(
            revisions,
            side="BUY",
            volume=Decimal(1),
            open_price=Decimal("1.1"),
            close_price=Decimal("1.101"),
            as_of=NOW + timedelta(hours=1),
            fx_evidence=None,
        ),
        operation="test.effective_revision",
    )
    assert result == Decimal("200.00")


def test_gap_overlap_or_unsupported_mode_blocks_calculation() -> None:
    """Unproved coverage and unsupported provider modes fail closed."""
    uncovered = revision()
    uncovered["complete_coverage"] = False
    assert (
        calculate_fx_profit(
            uncovered,
            side="BUY",
            volume=Decimal(1),
            open_price=Decimal("1.1"),
            close_price=Decimal("1.2"),
            as_of=NOW,
            fx_evidence=None,
        ).data
        is None
    )
    unsupported = revision(calculation_mode="CFD")
    assert (
        calculate_fx_profit(
            unsupported,
            side="BUY",
            volume=Decimal(1),
            open_price=Decimal("1.1"),
            close_price=Decimal("1.2"),
            as_of=NOW,
            fx_evidence=None,
        ).data
        is None
    )
