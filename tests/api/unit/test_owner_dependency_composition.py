"""API-to-owner dependency composition tests."""

import asyncio
from types import SimpleNamespace

import pytest
from app.services.api.composition import broker_session
from app.services.api.workstation.simulation import (
    orchestration as simulation_dependencies,
)
from app.services.api.workstation.trading import orchestration as trading_dependencies


def test_simulation_source_converts_and_delegates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The bridge converts the DTO and invokes only Simulator public functions."""
    converted = object()
    expected = object()
    calls: list[tuple[str, object]] = []
    monkeypatch.setattr(
        simulation_dependencies,
        "create_simulation_value",
        lambda contract, **values: calls.append((contract, values)) or converted,
    )
    monkeypatch.setattr(
        simulation_dependencies,
        "run_backtest_async",
        lambda request, auth, dependencies: _return_async(
            (request, auth, dependencies, expected)
        ),
    )
    source = simulation_dependencies.build_simulation_run_source("dependencies")
    boundary = SimpleNamespace(model_dump=lambda **_: {"request_id": "request-1"})
    result = asyncio.run(source("run", boundary, "auth"))
    assert calls == [("SimulationBacktestRequest", {"request_id": "request-1"})]
    assert result == (converted, "auth", "dependencies", expected)


def test_simulation_source_fails_closed_without_dependencies() -> None:
    """Missing Simulator reference resolvers never trigger speculative execution."""
    source = simulation_dependencies.build_simulation_run_source(None)
    boundary = SimpleNamespace(model_dump=lambda **_: {})
    with pytest.raises(RuntimeError, match="SIMULATION_RUNTIME_UNAVAILABLE"):
        asyncio.run(source("run", boundary, object()))


async def _return_async(value: object) -> object:
    """Return one value through a genuine coroutine."""
    return value


def test_trading_source_converts_and_delegates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The bridge delegates a validated mutation only to Trading public functions."""
    converted = object()
    expected = object()
    monkeypatch.setattr(
        trading_dependencies,
        "create_trading_request",
        lambda **_: converted,
    )

    async def submit(request: object, dependencies: object) -> object:
        assert (request, dependencies) == (converted, "dependencies")
        return expected

    monkeypatch.setattr(trading_dependencies, "submit_order", submit)
    source = trading_dependencies.build_trading_mutation_source("dependencies")
    boundary = SimpleNamespace(model_dump=lambda **_: {"action": "submit_order"})
    assert asyncio.run(source("submit_order", boundary, object())) is expected


def test_trading_source_dispatches_cancel_all_orders(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The bridge routes the bulk cancel-all action to Trading's own function."""
    converted = object()
    expected = object()
    monkeypatch.setattr(
        trading_dependencies,
        "create_trading_request",
        lambda **_: converted,
    )

    async def cancel_all(request: object, dependencies: object) -> object:
        assert (request, dependencies) == (converted, "dependencies")
        return expected

    monkeypatch.setattr(trading_dependencies, "cancel_all_orders", cancel_all)
    source = trading_dependencies.build_trading_mutation_source("dependencies")
    boundary = SimpleNamespace(model_dump=lambda **_: {"action": "cancel_all_orders"})
    assert asyncio.run(source("cancel_all_orders", boundary, object())) is expected


def test_broker_session_rejects_production_before_credentials() -> None:
    """Production broker connections remain outside the approved runtime boundary."""
    with pytest.raises(ValueError, match="production broker environments"):
        asyncio.run(
            broker_session.create_non_production_broker_session(
                credential_reference="missing-reference",
                owner_id="owner-1",
                key_set={},
                request_id="request-1",
                broker_id="mt5",
                environment="production",
            )
        )
