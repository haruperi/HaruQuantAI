"""Tests for the canonical backtest Simulator HTTP boundaries."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest
from app.services.api.identity import build_auth_context
from app.services.api.workstation.simulator.orchestration import (
    build_simulator_run_source,
    build_simulator_strategy_source,
)
from app.services.api.workstation.simulator.routes import (
    _cancel_run,
    _get_run,
    _list_runs,
    _list_strategies,
    _simulator_run_source,
    _simulator_strategy_source,
)
from app.services.api.workstation.simulator.schemas import SimulatorRunRequest
from app.utils import generate_id
from fastapi import HTTPException
from pydantic import ValidationError

_START = datetime(2025, 1, 1, tzinfo=UTC)
_END = datetime(2025, 3, 1, tzinfo=UTC)


def _context(*permissions: str) -> Any:
    """Return an authenticated principal carrying the given permissions.

    Returns:
        Validated authorization context.
    """
    return build_auth_context(
        principal={
            "principal_id": "user-backtest",
            "principal_type": "USER",
            "roles": ("researcher",),
            "permissions": permissions,
            "scopes": (),
            "tenant_or_environment": "development",
            "runtime_profile": "simulation",
        },
        trace={
            "issued_at": datetime.now(UTC),
            "request_id": generate_id("req"),
            "workflow_id": generate_id("wf"),
            "correlation_id": generate_id("cor"),
        },
    )


def _request(**overrides: Any) -> SimulatorRunRequest:
    """Build one valid boundary run request.

    Returns:
        Validated Simulator run request.
    """
    values: dict[str, Any] = {
        "symbol": "EURUSD",
        "timeframe": "H1",
        "start": _START,
        "end": _END,
        "strategy_id": "naive-ma-trend",
    }
    values.update(overrides)
    return SimulatorRunRequest(**values)


def test_uncomposed_sources_fail_closed() -> None:
    """Both Simulator dependencies refuse service until composed."""
    for dependency in (_simulator_strategy_source, _simulator_run_source):
        with pytest.raises(HTTPException) as raised:
            dependency()
        assert raised.value.status_code == 503
        assert raised.value.detail == "SIMULATOR_RUNTIME_UNAVAILABLE"


def test_strategy_catalogue_delegates_once_to_the_owner() -> None:
    """The catalogue route returns Simulation-owned descriptors unchanged."""
    payload = _list_strategies(
        _context("simulation:read"), build_simulator_strategy_source()
    )
    strategies = {item["strategy_id"] for item in payload["strategies"]}
    assert "naive-ma-trend" in strategies
    assert all("runnable" in item for item in payload["strategies"])


def test_reads_require_the_simulation_read_permission() -> None:
    """A principal without the read permission cannot list strategies."""
    with pytest.raises(HTTPException) as raised:
        _list_strategies(_context(), build_simulator_strategy_source())
    assert raised.value.status_code == 403


def test_an_uncomposed_registry_fails_the_run_surface_closed() -> None:
    """Every run operation reports the runtime as unavailable when uncomposed."""
    source = build_simulator_run_source(None)
    with pytest.raises(RuntimeError, match="SIMULATOR_RUNTIME_UNAVAILABLE"):
        source("list", principal_id="user-backtest")


def test_an_unknown_run_is_not_found() -> None:
    """Reading another principal's or an absent run fails closed with 404."""

    def source(operation: str, *args: object, **kwargs: object) -> object:
        del operation, args, kwargs
        return None

    with pytest.raises(HTTPException) as raised:
        _get_run("btr-missing", _context("simulation:read"), source)
    assert raised.value.status_code == 404
    assert raised.value.detail == "SIMULATOR_RUN_NOT_FOUND"

    with pytest.raises(HTTPException) as cancelled:
        _cancel_run("btr-missing", _context("simulation:run"), source)
    assert cancelled.value.status_code == 404


def test_run_listing_is_scoped_to_the_authenticated_principal() -> None:
    """The route passes only the caller's own identity to the owner."""
    seen: dict[str, object] = {}

    def source(operation: str, *args: object, **kwargs: object) -> object:
        del args
        seen["operation"] = operation
        seen["principal_id"] = kwargs.get("principal_id")
        return ()

    payload = _list_runs(_context("simulation:read"), source)
    assert payload == {"runs": ()}
    assert seen == {"operation": "list", "principal_id": "user-backtest"}


def test_the_request_schema_rejects_an_inverted_window() -> None:
    """A non-forward measurement window never reaches the owner."""
    with pytest.raises(ValidationError, match="start must be earlier than end"):
        _request(start=_END, end=_START)


def test_the_request_schema_bounds_parameters_and_currency() -> None:
    """Parameter and currency bounds are enforced at the boundary."""
    with pytest.raises(ValidationError):
        _request(account_currency="US")
    with pytest.raises(ValidationError, match="at most 32 parameters"):
        _request(parameters={f"p{index}": "1" for index in range(33)})
    with pytest.raises(ValidationError):
        _request(volume="0")
    assert _request(account_currency="usd").account_currency == "USD"


def test_the_request_schema_defaults_match_the_legacy_catalogue_run() -> None:
    """Defaults reproduce the legacy example's execution assumptions."""
    request = _request()
    assert request.initial_balance == Decimal("10000.00")
    assert request.volume == Decimal("0.1")
    assert request.commission_per_lot_per_side == 7
    assert request.spread_points == 10
    assert request.slippage_points == 1
    assert request.seed == 7
    assert request.timeframe == "H1"
