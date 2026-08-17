"""Account-mode execution-authority tests.

The elected account mode decides which venue an order actually reaches and
which Risk policy reviews it. These tests pin the two consequences that matter
for safety: a mode never trades a venue it is not labelled for, and the sim
route is refused outright rather than quietly served by a real broker.
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest
from app.services.api.workstation.trading import orchestration
from app.services.risk import build_personal_account_risk_config


class _StubBrokers:
    """Records how the mode-aware connector resolved and connected a broker."""

    def __init__(self, environment: str) -> None:
        """Initialize with the environment the configuration resolves to.

        Args:
            environment: MT5 environment the stub reports.
        """
        self.environment = environment
        self.resolved_allow_live: list[bool] = []
        self.connected_allow_live: list[bool] = []

    def resolve_provider_connection_config(
        self, _broker_id: str, *, allow_live: bool = False
    ) -> object:
        """Return a configuration naming the stub environment.

        Args:
            _broker_id: Requested broker identifier.
            allow_live: Whether live execution was elected.

        Returns:
            Structural configuration stand-in.
        """
        self.resolved_allow_live.append(allow_live)
        return SimpleNamespace(environment=self.environment)

    async def create_connected_broker(
        self, _broker_id: str, *, allow_live: bool = False
    ) -> object:
        """Return a connected adapter stand-in.

        Args:
            _broker_id: Requested broker identifier.
            allow_live: Whether live execution was elected.

        Returns:
            Opaque adapter stand-in.
        """
        self.connected_allow_live.append(allow_live)
        return SimpleNamespace(name="adapter")


def _install(monkeypatch: pytest.MonkeyPatch, brokers: _StubBrokers) -> None:
    """Install the stub as the Brokers module the connector imports.

    Args:
        monkeypatch: Test patcher.
        brokers: Stub recording resolution and connection.
    """
    import app.services.brokers as brokers_module

    monkeypatch.setattr(
        brokers_module,
        "resolve_provider_connection_config",
        brokers.resolve_provider_connection_config,
    )
    monkeypatch.setattr(
        brokers_module, "create_connected_broker", brokers.create_connected_broker
    )


def test_demo_mode_connects_demo_without_electing_live(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A demo-elected application never opts into a live connection."""
    brokers = _StubBrokers("demo")
    _install(monkeypatch, brokers)
    asyncio.run(orchestration._connect_mode_broker("demo"))
    assert brokers.resolved_allow_live == [False]
    assert brokers.connected_allow_live == [False]


def test_live_mode_elects_live_and_connects_live(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Electing LIVE is what opens the one documented live path."""
    brokers = _StubBrokers("live")
    _install(monkeypatch, brokers)
    asyncio.run(orchestration._connect_mode_broker("live"))
    assert brokers.resolved_allow_live == [True]
    assert brokers.connected_allow_live == [True]


def test_live_mode_with_demo_credentials_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The label and the credentials must agree.

    Demo and live are one execution path, so trading demo credentials while
    stamping every row live would make the registry marking that separates
    them a lie. It is refused before any order is reviewed.
    """
    brokers = _StubBrokers("demo")
    _install(monkeypatch, brokers)
    with pytest.raises(RuntimeError, match="ACCOUNT_MODE_CREDENTIAL_MISMATCH"):
        asyncio.run(orchestration._connect_mode_broker("live"))
    assert brokers.connected_allow_live == []


def test_demo_mode_with_live_credentials_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The mismatch check is symmetric: demo never trades a live account."""
    brokers = _StubBrokers("live")
    _install(monkeypatch, brokers)
    with pytest.raises(RuntimeError, match="ACCOUNT_MODE_CREDENTIAL_MISMATCH"):
        asyncio.run(orchestration._connect_mode_broker("demo"))
    assert brokers.connected_allow_live == []


def test_sim_mode_is_refused_rather_than_served_by_a_real_broker(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Sim has no composed venue, so it fails closed instead of reaching MT5."""
    brokers = _StubBrokers("demo")
    _install(monkeypatch, brokers)
    with pytest.raises(RuntimeError, match="SIM_EXECUTION_VENUE_UNAVAILABLE"):
        asyncio.run(orchestration._connect_mode_broker("sim"))
    assert brokers.resolved_allow_live == []
    assert brokers.connected_allow_live == []


@pytest.mark.parametrize(
    ("route", "profile"),
    [("sim", "simulation"), ("demo", "demo"), ("live", "live")],
)
def test_every_route_maps_to_its_risk_profile(route: str, profile: str) -> None:
    """Risk is scoped to the elected mode, not pinned to demo."""
    assert orchestration._RISK_PROFILE_BY_ROUTE[route] == profile


@pytest.mark.parametrize(
    ("profile", "route"), [("simulation", "sim"), ("demo", "demo")]
)
def test_risk_policy_builds_for_each_reviewable_mode(profile: str, route: str) -> None:
    """The same account thresholds apply, scoped to the mode under review."""
    config = build_personal_account_risk_config(profile, route)
    assert config.profile == profile
    assert config.execution_route == route


def test_live_risk_policy_contains_mandatory_safety_policy() -> None:
    """The owner-approved LIVE policy satisfies every fail-closed field."""
    config = build_personal_account_risk_config("live", "live")
    assert config.profile == "live"
    assert config.execution_route == "live"
    assert config.audit_persistence_required is True
    assert config.assessment_recalc_events
