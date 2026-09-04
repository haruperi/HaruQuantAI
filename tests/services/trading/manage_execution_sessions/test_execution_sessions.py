"""Unit tests for the trading execution sessions manager."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid7

import pytest
from app.contracts.trading.errors import TradingFailure
from app.contracts.trading.models import (
    ManageExecutionSessionsRequest,
    ManageExecutionSessionsSuccess,
)
from app.kernel.context import DefaultFeatureContext
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope
from app.services.trading.manage_execution_sessions.config import (
    ManageExecutionSessionsConfig,
)
from app.services.trading.manage_execution_sessions.execution_sessions import (
    ExecutionSessionsService,
)
from app.services.trading.manage_execution_sessions.feature import (
    ManageExecutionSessionsFeature,
)
from app.services.trading.manage_execution_sessions.manifest import SPEC

if TYPE_CHECKING:
    from pathlib import Path


def _request(operation: str, **kwargs: object) -> ManageExecutionSessionsRequest:
    """Build one operation request."""
    return ManageExecutionSessionsRequest(
        request_id=str(uuid7()),
        capability_snapshot_id=str(uuid7()),
        operation=operation,  # type: ignore[arg-type]
        **kwargs,  # type: ignore[arg-type]
    )


def test_manifest_spec() -> None:
    """Verify feature specification and declared durable state."""
    assert SPEC.feature_id == "FEAT-TRD-MANAGE_EXECUTION_SESSIONS"
    (provided,) = SPEC.provides
    assert provided.identifier == "trading.manage-execution-sessions@1"
    assert SPEC.state is not None
    assert SPEC.state.namespace == "trading.manage_execution_sessions"
    SPEC.validate()


def test_config_validation(tmp_path: Path) -> None:
    """Verify config rejects unknown keys and accepts valid path."""
    valid_db = tmp_path / "test.db"
    cfg = ManageExecutionSessionsConfig(database_path=valid_db)
    assert cfg.database_path == valid_db

    from app.services.trading.manage_execution_sessions.config import from_dict

    parsed = from_dict({"database_path": str(valid_db)})
    assert parsed.database_path == valid_db

    with pytest.raises(
        ValueError, match="Unknown manage-execution-sessions configuration keys"
    ):
        from_dict({"unknown_key": "val"})


@pytest.mark.asyncio
async def test_feature_mount_and_service(tmp_path: Path) -> None:
    """Verify feature mounts cleanly into context and registers cleanup."""
    db_file = tmp_path / "sessions.db"
    feat = ManageExecutionSessionsFeature()
    assert feat.service is None

    registry = ServiceRegistry()
    scope = FeatureScope(owner_id="FEAT-TRD-MANAGE_EXECUTION_SESSIONS")
    context = DefaultFeatureContext(
        spec=feat.spec,
        scope=scope,
        resolver=registry.resolve,
        provider_registrar=lambda cap, impl, sc: registry.register(
            cap, impl, owner_id=sc.owner_id, scope=sc
        ),
    )

    await feat.mount(context, {"database_path": str(db_file)})
    assert feat.service is not None

    # Test closing
    await scope.close()
    assert feat.service.closed is True


@pytest.mark.asyncio
async def test_session_lifecycle_and_actions(tmp_path: Path) -> None:
    """Verify listing, active/default, start, stop, and set_default."""
    db_file = tmp_path / "lifecycle.db"
    service = ExecutionSessionsService(
        ManageExecutionSessionsConfig(database_path=db_file)
    )

    # 1. List sessions - initially seeded with sim
    list_res = await service.manage_execution_sessions(
        _request("LIST_SESSIONS", principal_id="trader-1")
    )
    assert isinstance(list_res, ManageExecutionSessionsSuccess)
    assert len(list_res.sessions) >= 1
    session_ids = [s.session_id for s in list_res.sessions]
    sim_id = session_ids[0]

    # Mode filter
    sim_res = await service.manage_execution_sessions(
        _request("LIST_SESSIONS", principal_id="trader-1", mode="sim")
    )
    assert isinstance(sim_res, ManageExecutionSessionsSuccess)
    assert all(s.mode == "sim" for s in sim_res.sessions)

    # 2. Get active or default
    active_res = await service.manage_execution_sessions(
        _request("GET_ACTIVE_OR_DEFAULT", principal_id="trader-1")
    )
    assert isinstance(active_res, ManageExecutionSessionsSuccess)
    assert active_res.session is not None
    assert active_res.session.is_default is True

    # 3. Start session
    start_res = await service.manage_execution_sessions(
        _request("START_SESSION", session_id=sim_id)
    )
    assert isinstance(start_res, ManageExecutionSessionsSuccess)
    assert start_res.session is not None
    assert start_res.session.lifecycle_state == "running"
    assert start_res.session.is_active is True

    # 4. Stop session
    stop_res = await service.manage_execution_sessions(
        _request("STOP_SESSION", session_id=sim_id)
    )
    assert isinstance(stop_res, ManageExecutionSessionsSuccess)
    assert stop_res.session is not None
    assert stop_res.session.lifecycle_state == "stopped"
    assert stop_res.session.is_active is False

    # 5. Set default session
    default_res = await service.manage_execution_sessions(
        _request("SET_DEFAULT", session_id=sim_id, principal_id="trader-1")
    )
    assert isinstance(default_res, ManageExecutionSessionsSuccess)
    assert default_res.session is not None
    assert default_res.session.is_default is True

    service.close()


@pytest.mark.asyncio
async def test_session_error_handling(tmp_path: Path) -> None:
    """Verify failure modes on missing or non-existent sessions."""
    db_file = tmp_path / "errors.db"
    service = ExecutionSessionsService(
        ManageExecutionSessionsConfig(database_path=db_file)
    )

    # Missing session_id
    res_no_id = await service.manage_execution_sessions(_request("START_SESSION"))
    assert isinstance(res_no_id, TradingFailure)
    assert res_no_id.code == "TRADING_VALIDATION_FAILED"
    assert res_no_id.problem.status == 400

    # Non-existent session
    res_not_found = await service.manage_execution_sessions(
        _request("STOP_SESSION", session_id="non-existent-id")
    )
    assert isinstance(res_not_found, TradingFailure)
    assert res_not_found.code == "TRADING_STATE_CONFLICT"
    assert res_not_found.problem.status == 404
    assert res_not_found.problem.code == "SESSION_NOT_FOUND"

    # Unsupported operation bypassed via model_construct
    unsupported = await service.manage_execution_sessions(
        ManageExecutionSessionsRequest.model_construct(
            request_id=str(uuid7()),
            capability_snapshot_id=str(uuid7()),
            operation="INVALID_OP",
        )
    )
    assert isinstance(unsupported, TradingFailure)
    assert unsupported.code == "TRADING_QUERY_INVALID"
    assert unsupported.problem.status == 400

    service.close()


@pytest.mark.asyncio
async def test_account_profile_and_constraints(tmp_path: Path) -> None:
    """Verify account profile projections and instrument constraints."""
    db_file = tmp_path / "profile.db"
    service = ExecutionSessionsService(
        ManageExecutionSessionsConfig(database_path=db_file)
    )

    # Account profile
    profile_res = await service.manage_execution_sessions(
        _request(
            "GET_ACCOUNT_PROFILE",
            principal_id="user-42",
            username="test_trader",
        )
    )
    assert isinstance(profile_res, ManageExecutionSessionsSuccess)
    assert profile_res.profile is not None
    assert profile_res.profile.account_name == "test_trader"
    assert profile_res.profile.currency == "USD"
    assert profile_res.profile.balance > 0

    # Instrument constraints for seeded instrument
    eur_res = await service.manage_execution_sessions(
        _request("GET_INSTRUMENT_CONSTRAINTS", symbol="EURUSD")
    )
    assert isinstance(eur_res, ManageExecutionSessionsSuccess)
    assert eur_res.constraints is not None
    assert eur_res.constraints.symbol == "EURUSD"
    assert float(eur_res.constraints.min_quantity) > 0

    # Fallback for unseeded instrument
    unknown_res = await service.manage_execution_sessions(
        _request("GET_INSTRUMENT_CONSTRAINTS", symbol="UNKNOWN_SYM")
    )
    assert isinstance(unknown_res, ManageExecutionSessionsSuccess)
    assert unknown_res.constraints is not None
    assert unknown_res.constraints.symbol == "UNKNOWN_SYM"

    service.close()
