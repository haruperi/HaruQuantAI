"""Broker channel operational-state and REACH tests."""

from unittest.mock import Mock

import pytest
from app.services.brokers import (
    get_broker_environment_permission,
    get_broker_event_checkpoint,
    get_broker_route_recovery,
    persistence,
    record_binance_health_checkpoint,
    record_broker_event_checkpoint,
    record_broker_route_recovery,
    record_ctrader_health_checkpoint,
    record_dukascopy_health_checkpoint,
    record_metatrader_health_checkpoint,
    record_yahoo_health_checkpoint,
    register_broker_environment_permission,
)
from app.services.brokers._shared import health
from app.services.brokers._shared.state import (
    _account_digest,
    _optional_decimal,
    _text,
)
from app.services.brokers.environment_guards import permissions
from app.services.brokers.events import checkpoints as event_checkpoints
from app.services.brokers.persistence import create as persistence_create
from app.services.brokers.reconciliation import checkpoints as route_checkpoints

_RESULT = object()


@pytest.mark.parametrize(
    ("operation", "provider"),
    [
        (record_metatrader_health_checkpoint, "mt5"),
        (record_ctrader_health_checkpoint, "ctrader"),
        (record_binance_health_checkpoint, "binance_spot"),
        (record_dukascopy_health_checkpoint, "dukascopy"),
        (record_yahoo_health_checkpoint, "yahoo"),
    ],
)
def test_each_channel_reaches_health_history(
    monkeypatch: pytest.MonkeyPatch, operation: object, provider: str
) -> None:
    """Reach health persistence through every production channel operation."""
    recorder = Mock(return_value=_RESULT)
    monkeypatch.setattr(health, "create_health_record", recorder)
    result = operation(  # type: ignore[operator]
        account_reference="account-1",
        environment="sandbox",
        health_status="READY",
        latency_ms="1.25",
        error_rate="0",
        maintenance=False,
        route_ready=True,
        observed_at="2026-08-10T00:00:00+00:00",
        request_id="req-health",
    )
    assert result is _RESULT
    parameters = recorder.call_args.args[0]
    assert parameters[1] == provider
    assert parameters[2] != "account-1"


def test_environment_permission_table_has_production_reach(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reach permission create/read without retaining the account reference."""
    create = Mock(return_value=_RESULT)
    read = Mock(return_value=_RESULT)
    monkeypatch.setattr(permissions, "create_environment_permission_record", create)
    monkeypatch.setattr(permissions, "read_environment_permission", read)
    assert (
        register_broker_environment_permission(
            "mt5",
            "account-1",
            "demo",
            allow_read=True,
            allow_mutation=True,
            effective_from="2026-08-10T00:00:00+00:00",
            request_id="req-permission",
        )
        is _RESULT
    )
    assert (
        get_broker_environment_permission(
            "mt5",
            "account-1",
            "demo",
            as_of="2026-08-10T00:00:00+00:00",
            request_id="req-read",
        )
        is _RESULT
    )
    assert create.call_args.args[0][2] != "account-1"
    with pytest.raises(ValueError, match="Trading admission"):
        register_broker_environment_permission(
            "mt5",
            "account-1",
            "live",
            allow_read=True,
            allow_mutation=True,
            effective_from="2026-08-10T00:00:00+00:00",
            request_id="req-live",
        )


def test_route_recovery_table_has_production_reach(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reach route recovery upsert/read through package-root operations."""
    write = Mock(return_value=_RESULT)
    read = Mock(return_value=_RESULT)
    monkeypatch.setattr(route_checkpoints, "upsert_route_recovery_record", write)
    monkeypatch.setattr(route_checkpoints, "read_route_recovery", read)
    assert (
        record_broker_route_recovery(
            "route-1",
            "mt5",
            "account-1",
            "demo",
            "cursor-1",
            "KNOWN",
            request_id="req-route",
        )
        is _RESULT
    )
    assert get_broker_route_recovery("route-1", request_id="req-read") is _RESULT


def test_event_checkpoint_table_has_production_reach(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reach event checkpoint upsert/read through package-root operations."""
    write = Mock(return_value=_RESULT)
    read = Mock(return_value=_RESULT)
    monkeypatch.setattr(event_checkpoints, "upsert_event_checkpoint_record", write)
    monkeypatch.setattr(event_checkpoints, "read_event_checkpoint", read)
    assert (
        record_broker_event_checkpoint(
            "ctrader",
            "account-1",
            "orders",
            "cursor-1",
            "digest-1",
            source_sequence=1,
            request_id="req-event",
        )
        is _RESULT
    )
    assert (
        get_broker_event_checkpoint(
            "ctrader",
            "account-1",
            "orders",
            request_id="req-read",
        )
        is _RESULT
    )
    with pytest.raises(ValueError, match="non-negative"):
        record_broker_event_checkpoint(
            "ctrader",
            "account-1",
            "orders",
            "cursor-1",
            "digest-1",
            source_sequence=-1,
            request_id="req-event",
        )


def test_persistence_exports_remain_callable() -> None:
    """Keep every checkpoint CRUD operation callable at its support boundary."""
    for name in (
        "create_health_record",
        "create_environment_permission_record",
        "read_environment_permission",
        "read_route_recovery",
        "read_event_checkpoint",
        "upsert_route_recovery_record",
        "upsert_event_checkpoint_record",
    ):
        assert callable(getattr(persistence, name))


def test_checkpoint_create_builders_delegate_to_data(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Exercise both new create executors at their persistence boundary."""
    execute = Mock(return_value=_RESULT)
    monkeypatch.setattr(persistence_create, "_execute", execute)
    parameters = ("record-1",)
    assert (
        persistence_create.create_health_record(parameters, request_id="req-health")
        is _RESULT
    )
    assert (
        persistence_create.create_environment_permission_record(
            parameters, request_id="req-permission"
        )
        is _RESULT
    )


def test_feature_checkpoint_delegates_reach_persistence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Exercise lazy feature-to-persistence delegation without database I/O."""
    create_health = Mock(return_value=_RESULT)
    create_permission = Mock(return_value=_RESULT)
    read_permission = Mock(return_value=_RESULT)
    write_event = Mock(return_value=_RESULT)
    read_event = Mock(return_value=_RESULT)
    write_route = Mock(return_value=_RESULT)
    read_route = Mock(return_value=_RESULT)
    monkeypatch.setattr(persistence, "create_health_record", create_health)
    monkeypatch.setattr(
        persistence, "create_environment_permission_record", create_permission
    )
    monkeypatch.setattr(persistence, "read_environment_permission", read_permission)
    monkeypatch.setattr(persistence, "upsert_event_checkpoint_record", write_event)
    monkeypatch.setattr(persistence, "read_event_checkpoint", read_event)
    monkeypatch.setattr(persistence, "upsert_route_recovery_record", write_route)
    monkeypatch.setattr(persistence, "read_route_recovery", read_route)

    assert health.create_health_record(("health",), request_id="req") is _RESULT
    assert (
        permissions.create_environment_permission_record(
            ("permission",), request_id="req"
        )
        is _RESULT
    )
    assert (
        permissions.read_environment_permission(
            "mt5", "digest", "demo", "2026-08-10T00:00:00Z", request_id="req"
        )
        is _RESULT
    )
    assert (
        event_checkpoints.upsert_event_checkpoint_record(("event",), request_id="req")
        is _RESULT
    )
    assert (
        event_checkpoints.read_event_checkpoint(
            "mt5", "digest", "orders", request_id="req"
        )
        is _RESULT
    )
    assert (
        route_checkpoints.upsert_route_recovery_record(("route",), request_id="req")
        is _RESULT
    )
    assert route_checkpoints.read_route_recovery("route", request_id="req") is _RESULT


def test_checkpoint_state_validation_is_fail_closed() -> None:
    """Validate redaction helpers and reject malformed checkpoint evidence."""
    assert len(_account_digest(" account-1 ")) == 64
    assert _optional_decimal(None, "latency_ms") is None
    assert _optional_decimal("1.25", "latency_ms") == "1.25"
    with pytest.raises(ValueError, match=r"1\.\.256"):
        _text("", "provider")
    with pytest.raises(ValueError, match="decimal-compatible"):
        _optional_decimal("not-a-decimal", "latency_ms")
    with pytest.raises(ValueError, match="finite and non-negative"):
        _optional_decimal("-1", "latency_ms")
