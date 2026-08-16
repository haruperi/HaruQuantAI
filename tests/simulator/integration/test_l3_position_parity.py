"""End-to-end Simulation position authority evidence for the L3 parity gate."""

from decimal import Decimal

from app.services.trading import create_position_authority_event

from tests.simulator.component.test_engine import _engine, _intent, _tick, _value


def test_open_and_close_deals_preserve_post_event_authority(tmp_path: object) -> None:
    """Engine snapshots retain Trading-compatible OPEN and FLAT deal evidence."""
    engine = _engine(tmp_path, "l3-authority")  # type: ignore[arg-type]
    engine.submit_order(_intent())
    first_tick = _tick()
    _value(engine.execute_tick(first_tick))
    _value(engine.close_position("sim-position-order-engine", Decimal(1)))
    snapshot = _value(engine.snapshot())
    deals = snapshot["deals"]
    assert len(deals) == 2
    events = tuple(
        create_position_authority_event(**deal["trading_authority_event"])
        for deal in deals
    )
    assert (events[0].state, events[0].quantity) == ("OPEN", Decimal(1))
    assert (events[1].state, events[1].quantity) == ("FLAT", Decimal(0))
    assert events[0].source_sequence < events[1].source_sequence
    assert events[0].available_at == events[1].available_at
    assert all(deal["authority_snapshot"]["account"] for deal in deals)
    assert all(str(deal["ledger_reference"]).startswith("ledger-") for deal in deals)
