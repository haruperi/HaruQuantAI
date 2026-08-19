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
from app.services.api.widgets.trading import orchestration, routes
from app.services.api.widgets.trading.schemas import ExecutionSessionActionRequest
from app.services.risk import build_personal_account_risk_config
from fastapi import HTTPException


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


def test_sim_session_start_is_blocked_when_system_mode_is_demo(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The SIM start path cannot bypass the authoritative system mode."""
    auth = SimpleNamespace(principal_id="owner", tenant_or_environment="dev")
    session = SimpleNamespace(
        session_id="session-sim",
        mode="sim",
        simulation_session_id="owner_1",
    )
    monkeypatch.setattr(routes, "require_human_permission", lambda *_: None)
    monkeypatch.setattr(routes, "_owned_session", lambda *_: session)

    async def _profile(_auth: object) -> object:
        return SimpleNamespace(selected_mode="demo", mode_compatible=True)

    async def _start(
        _session_id: str,
        *,
        expected_version: int,
        authority_start: object,
        request_id: str,
    ) -> object:
        del expected_version, request_id
        evidence = await authority_start({})  # type: ignore[operator]
        assert evidence["verified"] is False
        raise ValueError("execution session authority verification failed")

    monkeypatch.setattr(routes, "start_execution_session", _start)
    with pytest.raises(HTTPException) as raised:
        asyncio.run(
            routes._start_execution_session(
                "session-sim",
                ExecutionSessionActionRequest(expected_version=0),
                auth,
                _profile,
            )
        )
    assert raised.value.status_code == 409
    assert raised.value.detail == "execution session authority verification failed"


def test_configured_non_default_sim_candidate_can_start(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A stopped SIM candidate is verified from itself, not Header selection."""
    auth = SimpleNamespace(principal_id="owner", tenant_or_environment="dev")
    session = SimpleNamespace(
        session_id="session-sim",
        mode="sim",
        provider_account_ref="owner",
        simulation_session_id="owner_1",
        dataset_ref="dataset-one",
        dataset_revision="revision-one",
        dataset_hash="a" * 64,
        sim_initial_balance="100000",
        sim_leverage=100,
        sim_account_currency="USD",
    )
    monkeypatch.setattr(routes, "require_human_permission", lambda *_: None)
    monkeypatch.setattr(routes, "_owned_session", lambda *_: session)
    monkeypatch.setattr(
        routes,
        "list_verified_datasets",
        lambda **_: (
            {
                "dataset_id": "dataset-one",
                "revision": "revision-one",
                "content_hash": "a" * 64,
            },
        ),
    )

    async def _profile(_auth: object) -> object:
        return SimpleNamespace(
            selected_mode="sim",
            mode_compatible=False,
            account_name="owner",
        )

    async def _start(
        _session_id: str,
        *,
        expected_version: int,
        authority_start: object,
        request_id: str,
    ) -> object:
        del expected_version, request_id
        evidence = await authority_start({})  # type: ignore[operator]
        assert evidence["verified"] is True
        return session

    monkeypatch.setattr(routes, "start_execution_session", _start)
    result = asyncio.run(
        routes._start_execution_session(
            "session-sim",
            ExecutionSessionActionRequest(expected_version=6),
            auth,
            _profile,
        )
    )
    assert result is session


@pytest.mark.parametrize("missing_identity", [True, False])
def test_sim_candidate_rejects_missing_configuration_or_stale_dataset(
    monkeypatch: pytest.MonkeyPatch, missing_identity: bool
) -> None:
    """Candidate identity and exact current dataset lineage are both mandatory."""
    auth = SimpleNamespace(principal_id="owner", tenant_or_environment="dev")
    session = SimpleNamespace(
        session_id="session-sim",
        mode="sim",
        provider_account_ref=None if missing_identity else "owner",
        simulation_session_id="owner_1",
        dataset_ref="dataset-one",
        dataset_revision="revision-one",
        dataset_hash="a" * 64,
        sim_initial_balance="100000",
        sim_leverage=100,
        sim_account_currency="USD",
    )
    monkeypatch.setattr(routes, "require_human_permission", lambda *_: None)
    monkeypatch.setattr(routes, "_owned_session", lambda *_: session)
    monkeypatch.setattr(
        routes,
        "list_verified_datasets",
        lambda **_: (
            {
                "dataset_id": "dataset-one",
                "revision": "revision-one",
                "content_hash": ("a" if missing_identity else "b") * 64,
            },
        ),
    )

    async def _profile(_auth: object) -> object:
        return SimpleNamespace(
            selected_mode="sim",
            mode_compatible=False,
            account_name="owner",
        )

    async def _start(
        _session_id: str,
        *,
        expected_version: int,
        authority_start: object,
        request_id: str,
    ) -> object:
        del expected_version, request_id
        evidence = await authority_start({})  # type: ignore[operator]
        assert evidence["verified"] is False
        raise ValueError("execution session authority verification failed")

    monkeypatch.setattr(routes, "start_execution_session", _start)
    with pytest.raises(HTTPException) as raised:
        asyncio.run(
            routes._start_execution_session(
                "session-sim",
                ExecutionSessionActionRequest(expected_version=6),
                auth,
                _profile,
            )
        )
    assert raised.value.status_code == 409


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


@pytest.mark.parametrize(
    ("route", "platform_mode"),
    [("sim", "SIMULATION"), ("demo", "DEMO"), ("live", "REAL")],
)
def test_platform_mode_gate_accepts_exact_pairs(
    monkeypatch: pytest.MonkeyPatch, route: str, platform_mode: str
) -> None:
    """Only the three exact owner-approved mode pairs are admitted."""

    async def _read(_route: str) -> str:
        return platform_mode

    monkeypatch.setattr(orchestration, "_read_platform_trade_mode", _read)
    asyncio.run(orchestration._require_platform_mode_match(route))


@pytest.mark.parametrize(
    ("route", "platform_mode"),
    [("live", "DEMO"), ("demo", "REAL"), ("sim", "DEMO"), ("demo", "CONTEST")],
)
def test_platform_mode_gate_rejects_every_mismatch(
    monkeypatch: pytest.MonkeyPatch, route: str, platform_mode: str
) -> None:
    """Mismatched or unsupported platform evidence fails closed."""

    async def _read(_route: str) -> str:
        return platform_mode

    monkeypatch.setattr(orchestration, "_read_platform_trade_mode", _read)
    with pytest.raises(RuntimeError, match="ACCOUNT_MODE_PLATFORM_MISMATCH"):
        asyncio.run(orchestration._require_platform_mode_match(route))
