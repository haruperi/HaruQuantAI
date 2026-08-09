"""Fail-closed assistance and override policy for simulation modes."""

# ruff: noqa: TC001

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType

from app.services.simulator.checklists.contracts import SimulationMode

_MODE_POLICIES: Mapping[SimulationMode, Mapping[str, object]] = MappingProxyType(
    {
        "Guided": MappingProxyType(
            {
                "hints": "proactive",
                "sequencing": "enforced",
                "bypass_optional": False,
                "override": False,
                "scored": False,
                "rewind": True,
            }
        ),
        "Standard": MappingProxyType(
            {
                "hints": "on_request",
                "sequencing": "enforced",
                "bypass_optional": True,
                "override": False,
                "scored": False,
                "rewind": True,
            }
        ),
        "Expert": MappingProxyType(
            {
                "hints": "disabled",
                "sequencing": "advisory",
                "bypass_optional": True,
                "override": False,
                "scored": False,
                "rewind": True,
            }
        ),
        "Challenge": MappingProxyType(
            {
                "hints": "disabled",
                "sequencing": "enforced",
                "bypass_optional": False,
                "override": False,
                "scored": True,
                "rewind": False,
            }
        ),
    }
)


def get_simulation_mode_policy(mode: SimulationMode) -> Mapping[str, object]:
    """Return immutable policy for one simulation mode.

    Args:
        mode: Supported simulation mode.

    Returns:
        Immutable policy including route-isolation evidence.

    Raises:
        ValueError: If the mode is unsupported.
    """
    try:
        policy = dict(_MODE_POLICIES[mode])
    except KeyError as error:
        raise ValueError("unsupported simulation mode") from error
    policy.update({"route": "sim", "live_route_allowed": False})
    return MappingProxyType(policy)


__all__ = ["get_simulation_mode_policy"]
