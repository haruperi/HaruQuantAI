"""Cross-domain proof that every Simulator mode remains simulation-only."""

import pytest
from app.services.simulator import get_simulation_mode_policy


@pytest.mark.parametrize("mode", ["Guided", "Standard", "Expert", "Challenge"])
def test_simulation_mode_never_grants_live_route(mode: str) -> None:
    """Require every mode to carry an immutable simulation-only route verdict."""
    policy = get_simulation_mode_policy(mode)
    assert policy["route"] == "sim"
    assert policy["live_route_allowed"] is False
    assert policy["override"] is False
