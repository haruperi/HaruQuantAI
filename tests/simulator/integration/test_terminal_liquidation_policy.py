"""Hashed terminal-liquidation policy integration evidence."""

from decimal import Decimal

import pytest
from app.services.simulator.run.contracts import SimulationBacktestRequest
from app.services.simulator.run.orchestrator import finalize_open_positions

POSITION = {"position_id": "position-1", "volume": Decimal(1)}


class _Dependencies:
    """Capture terminal requests at the public Trading boundary."""

    def __init__(self) -> None:
        self.positions: list[object] = []

    async def execute_terminal_action(
        self, position: object, engine: object, request: object
    ) -> object:
        """Record one Risk-authorized terminal action."""
        del engine, request
        self.positions.append(position)
        return {"status": "accepted"}


@pytest.mark.anyio
@pytest.mark.parametrize(("enabled", "expected"), [(False, 0), (True, 1)])
async def test_terminal_liquidation_runs_only_when_hashed_policy_enables_it(
    enabled: bool, expected: int
) -> None:
    """V2 policy off preserves exposure; policy on uses Trading exactly once."""
    request = SimulationBacktestRequest.model_construct(
        close_open_positions_at_end=enabled
    )
    dependencies = _Dependencies()
    count = await finalize_open_positions(
        request,
        dependencies,
        object(),
        (POSITION,),  # type: ignore[arg-type]
    )
    assert count == expected
    assert len(dependencies.positions) == expected
