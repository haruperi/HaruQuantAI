"""Tests for canonical application composition and lifecycle."""

from types import SimpleNamespace
from typing import Any

import pytest
from app.services.api import (
    build_api_settings,
    build_in_process_api_graph,
    create_api_app,
    get_required_in_process_provider_names,
)
from app.services.api.composition import application, lifecycle, runtime_settings
from app.services.api.composition.owner_sources import (
    read_audit_events,
    read_dashboard_snapshot,
    read_trading_events,
)
from app.services.api.workstation.dashboards.routes import _dashboard_source
from app.services.api.workstation.operator.routes import _audit_source, _event_source
from fastapi.testclient import TestClient

from tests.api._support import get_json, post_json


@pytest.fixture(autouse=True)
def _stub_lifecycle_storage_dependencies(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep lifecycle unit tests isolated from database-backed startup work."""

    def success(_: object) -> SimpleNamespace:
        """Return one successful inert migration response."""
        return SimpleNamespace(status="success", data=object())

    def runtime_settings(*, request_id: str) -> object:
        """Return an inert snapshot for one canonical startup request."""
        assert request_id.startswith("req-")
        return object()

    monkeypatch.setattr(lifecycle, "run_indicators_migrations", success)
    monkeypatch.setattr(lifecycle, "run_broker_migrations", success)
    monkeypatch.setattr(lifecycle, "run_simulator_migrations", success)
    monkeypatch.setattr(lifecycle, "run_analytics_migrations", success)
    monkeypatch.setattr(lifecycle, "run_optimization_migrations", success)
    monkeypatch.setattr(lifecycle, "run_portfolio_migrations", success)
    monkeypatch.setattr(
        lifecycle,
        "load_runtime_settings_snapshot",
        runtime_settings,
    )
    monkeypatch.setattr(lifecycle, "activate_runtime_logging", lambda _: None)
    monkeypatch.setattr(
        lifecycle,
        "close_data_provider_sessions",
        lambda _: SimpleNamespace(status="success"),
    )
    monkeypatch.setattr(
        lifecycle, "build_runtime_provider_settings", lambda _: object()
    )


def _in_process_providers() -> dict[str, object]:
    """Build complete inert provider values for lifecycle tests."""
    return {
        name: lambda *args, **kwargs: (args, kwargs)
        for name in get_required_in_process_provider_names()
    }


@pytest.mark.parametrize("level", ["INFO", "ERROR"])
def test_database_logging_level_is_activated(
    monkeypatch: pytest.MonkeyPatch,
    level: str,
) -> None:
    """Activate a validated logging level from the global settings snapshot."""
    configured: list[Any] = []
    monkeypatch.setattr(
        runtime_settings,
        "get_system_settings",
        lambda **_: SimpleNamespace(settings={"LOG_LEVEL": level}, version=3),
    )
    monkeypatch.setattr(runtime_settings, "configure_logging", configured.append)

    snapshot = runtime_settings.load_runtime_settings_snapshot(request_id="req-test")
    runtime_settings.activate_runtime_logging(snapshot)

    assert len(configured) == 1
    assert configured[0].level == level


def test_database_logging_level_defaults_to_info(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Use the safe INFO bootstrap when the global document omits LOG_LEVEL."""
    configured: list[Any] = []
    monkeypatch.setattr(
        runtime_settings,
        "get_system_settings",
        lambda **_: SimpleNamespace(settings={}, version=1),
    )
    monkeypatch.setattr(runtime_settings, "configure_logging", configured.append)

    snapshot = runtime_settings.load_runtime_settings_snapshot(request_id="req-test")
    runtime_settings.activate_runtime_logging(snapshot)

    assert configured[0].level == "INFO"


def test_invalid_database_logging_level_blocks_activation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reject an invalid persisted logging policy without changing handlers."""
    monkeypatch.setattr(
        runtime_settings,
        "get_system_settings",
        lambda **_: SimpleNamespace(settings={"LOG_LEVEL": "TRACE"}, version=2),
    )
    configured: list[Any] = []
    monkeypatch.setattr(runtime_settings, "configure_logging", configured.append)

    snapshot = runtime_settings.load_runtime_settings_snapshot(request_id="req-test")
    with pytest.raises(ValueError, match="LOG_LEVEL_INVALID"):
        runtime_settings.activate_runtime_logging(snapshot)
    assert configured == []


def test_database_provider_settings_are_validated(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Translate only approved global provider values into an opaque snapshot."""
    monkeypatch.setattr(
        runtime_settings,
        "get_system_settings",
        lambda **_: SimpleNamespace(
            settings={
                "MT5_ENABLED": "true",
                "MT5_TERMINAL_PATH": "terminal64.exe",
                "APP_NAME": "ignored",
            },
            version=4,
        ),
    )

    snapshot = runtime_settings.load_runtime_settings_snapshot(request_id="req-test")
    providers = runtime_settings.build_runtime_provider_settings(snapshot)

    assert providers.mt5_enabled is True
    assert providers.mt5_terminal_path.get_secret_value() == "terminal64.exe"
    assert providers.ctrader_enabled is False


def test_canonical_app_has_exact_cors_and_route_catalog() -> None:
    """One app exposes every registered route under `/api/v1`."""
    config = build_api_settings(ui_origins=("https://ui.example.test",))
    app = create_api_app(config)
    paths = app.openapi()["paths"]
    assert "/api/v1/auth/login" in paths
    assert "/api/v1/auth/me" in paths
    assert "/api/v1/indicators" in paths
    assert len(paths) == 84
    assert "/api/v1/data/bars" in paths
    assert "/api/v1/portfolio/{portfolio_id}/activate" in paths
    assert "/api/v1/portfolio/{portfolio_id}/rollback" in paths
    assert "/api/v1/portfolio/{portfolio_id}/drift" in paths
    assert "/api/v1/portfolio/rebalance" in paths
    assert "/api/v1/portfolio/measurement/recompute" in paths
    assert "/api/v1/portfolio/{portfolio_id}/definitions" in paths
    assert "/api/v1/portfolio/{portfolio_id}/definitions/{portfolio_version}" in paths
    assert "/api/v1/data/datasets/prepare" in paths
    assert "/api/v1/data/imports" in paths
    assert "/api/v1/simulation/live-sessions" in paths
    assert "/api/v1/simulation/live-sessions/{session_id}" in paths
    assert "/api/v1/data/imports/dialects" in paths
    assert "/api/v1/strategies/{strategy_id}/parameters" in paths
    assert "/api/v1/operator/approvals" in paths
    assert "/api/v1/workstation" in paths
    assert "/api/v1/workstation/commands" in paths
    assert "/api/v1/operator/kill-switch" not in paths
    assert "/api/v1/backtest/run" not in paths
    assert all(path.startswith("/api/v1/") for path in paths)
    cors = next(
        middleware
        for middleware in app.user_middleware
        if middleware.cls.__name__ == "CORSMiddleware"
    )
    assert cors.kwargs["allow_origins"] == ["https://ui.example.test"]
    assert application.app is not None


def test_canonical_app_binds_exact_owner_sources() -> None:
    """The default ASGI application uses the concrete reduced owner graph."""
    app = create_api_app(build_api_settings())
    assert app.dependency_overrides[_dashboard_source]() is read_dashboard_snapshot
    assert app.dependency_overrides[_audit_source]() is read_audit_events
    assert app.dependency_overrides[_event_source]() is read_trading_events


def test_runtime_profile_and_execution_route_fail_closed() -> None:
    """Reject mismatched routes and live execution without explicit enablement."""
    with pytest.raises(ValueError, match="runtime profile"):
        build_api_settings(runtime_profile="simulation", execution_route="demo")
    with pytest.raises(ValueError, match="live execution"):
        build_api_settings(
            runtime_profile="live",
            execution_route="live",
            allow_live_mutations=False,
        )
    settings = build_api_settings(
        runtime_profile="live",
        execution_route="live",
        allow_live_mutations=True,
    )
    assert settings.allow_live_mutations is True


def test_canonical_app_fails_closed_before_owner_delegation() -> None:
    """Protected and idempotent routes reject incomplete boundary evidence."""
    app = create_api_app(build_api_settings(dev_auto_login=False))
    auth_status, auth_body = get_json(app, "/api/v1/health/readiness")
    assert auth_status == 401
    assert auth_body["status"] == "error"
    assert auth_body["error"]["code"] == "AUTHENTICATION_REQUIRED"
    assert auth_body["metadata"]["route"] == "/api/v1/health/readiness"
    excluded_status, excluded_body = post_json(
        app,
        "/api/v1/portfolio/activations",
        {},
    )
    assert excluded_status == 404
    assert excluded_body["status"] == "error"


def test_canonical_app_wraps_successful_json_responses() -> None:
    """Every non-stream JSON success uses the canonical five-field envelope."""
    app = create_api_app(build_api_settings())
    response_status, response_body = get_json(app, "/api/v1/health/liveness")
    assert response_status == 200
    assert set(response_body) == {"status", "message", "data", "error", "metadata"}
    assert response_body["status"] == "success"
    assert response_body["error"] is None
    assert response_body["metadata"]["operation"] == "api.get_liveness"


def test_framework_documentation_responses_remain_raw() -> None:
    """Serve Swagger and its OpenAPI document outside the API envelope."""
    app = create_api_app(build_api_settings())
    client = TestClient(app)
    schema = client.get("/openapi.json")
    docs = client.get("/docs")
    assert schema.status_code == 200
    assert schema.json()["openapi"].startswith("3.")
    assert "data" not in schema.json()
    assert docs.status_code == 200
    assert "/openapi.json" in docs.text


def test_unknown_route_returns_not_found_envelope() -> None:
    """Classify an unknown application path as a stable not-found error."""
    app = create_api_app(build_api_settings())
    response_status, response_body = get_json(app, "/")
    assert response_status == 404
    assert response_body["status"] == "error"
    assert response_body["error"]["code"] == "NOT_FOUND"
    assert response_body["metadata"]["operation"] == "api.unknown"


def test_required_startup_failure_propagates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Required storage failure blocks startup truthfully."""
    monkeypatch.setattr(
        lifecycle,
        "run_api_migrations",
        lambda _: SimpleNamespace(status="error", data=None),
    )
    app = create_api_app(build_api_settings())

    async def enter_lifespan() -> None:
        async with lifecycle.lifespan(app):
            raise AssertionError("startup failure must prevent serving")

    import asyncio

    with pytest.raises(lifecycle.StartupError):
        asyncio.run(enter_lifespan())


def test_invalid_runtime_logging_blocks_startup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Invalid persisted logging policy prevents the API becoming ready."""
    monkeypatch.setattr(
        lifecycle,
        "run_api_migrations",
        lambda _: SimpleNamespace(status="success", data=object()),
    )
    monkeypatch.setattr(
        lifecycle,
        "activate_runtime_logging",
        lambda _: (_ for _ in ()).throw(ValueError("LOG_LEVEL_INVALID")),
    )
    app = create_api_app(build_api_settings())

    async def enter_lifespan() -> None:
        async with lifecycle.lifespan(app):
            raise AssertionError("invalid logging must prevent serving")

    import asyncio

    with pytest.raises(
        lifecycle.StartupError,
        match="API_LOGGING_CONFIGURATION_INVALID",
    ):
        asyncio.run(enter_lifespan())
    assert app.state.api_ready is False


def test_simulator_storage_failure_blocks_startup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Simulator migration failure blocks API readiness fail closed."""
    monkeypatch.setattr(
        lifecycle,
        "run_api_migrations",
        lambda _: SimpleNamespace(status="success", data=object()),
    )
    monkeypatch.setattr(
        lifecycle,
        "run_simulator_migrations",
        lambda _: SimpleNamespace(status="error", data=None),
    )
    app = create_api_app(build_api_settings())

    async def enter_lifespan() -> None:
        async with lifecycle.lifespan(app):
            raise AssertionError("startup failure must prevent serving")

    import asyncio

    with pytest.raises(
        lifecycle.StartupError,
        match="SIMULATOR_STORAGE_INITIALIZATION_FAILED",
    ):
        asyncio.run(enter_lifespan())
    assert app.state.api_ready is False


def test_brokers_storage_failure_blocks_startup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Brokers migration failure blocks API readiness fail closed."""
    monkeypatch.setattr(
        lifecycle,
        "run_broker_migrations",
        lambda _: SimpleNamespace(status="error", data=None),
    )
    app = create_api_app(build_api_settings())

    async def enter_lifespan() -> None:
        async with lifecycle.lifespan(app):
            raise AssertionError("startup failure must prevent serving")

    import asyncio

    with pytest.raises(
        lifecycle.StartupError,
        match="BROKERS_STORAGE_INITIALIZATION_FAILED",
    ):
        asyncio.run(enter_lifespan())
    assert app.state.api_ready is False


def test_optional_startup_failure_is_visible_degradation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Explicit optional failures degrade but do not block serving."""
    monkeypatch.setattr(
        lifecycle,
        "run_api_migrations",
        lambda _: SimpleNamespace(status="success", data=object()),
    )
    app = application.create_app(
        build_api_settings(),
        optional_startup_probes={
            "optional": lambda: (_ for _ in ()).throw(RuntimeError())
        },
    )

    async def enter_lifespan() -> None:
        async with lifecycle.lifespan(app):
            assert app.state.api_ready is True
            assert app.state.api_optional_degraded == {
                "optional": "DEPENDENCY_UNAVAILABLE"
            }
        assert app.state.api_ready is False

    import asyncio

    asyncio.run(enter_lifespan())


def test_analytics_storage_failure_blocks_startup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Analytics migration failure blocks API readiness fail closed."""
    monkeypatch.setattr(
        lifecycle,
        "run_api_migrations",
        lambda _: SimpleNamespace(status="success", data=object()),
    )
    monkeypatch.setattr(
        lifecycle,
        "run_analytics_migrations",
        lambda _: SimpleNamespace(status="error", data=None),
    )
    app = create_api_app(build_api_settings())

    async def enter_lifespan() -> None:
        async with lifecycle.lifespan(app):
            raise AssertionError("startup failure must prevent serving")

    import asyncio

    with pytest.raises(
        lifecycle.StartupError,
        match="ANALYTICS_STORAGE_INITIALIZATION_FAILED",
    ):
        asyncio.run(enter_lifespan())
    assert app.state.api_ready is False


def test_required_provider_failure_blocks_readiness(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A failed required in-process probe prevents application readiness."""
    monkeypatch.setattr(
        lifecycle,
        "run_api_migrations",
        lambda _: SimpleNamespace(status="success", data=object()),
    )
    app = create_api_app(build_api_settings())

    def unavailable() -> object:
        """Represent one unavailable required provider."""
        raise RuntimeError

    app.state.api_required_startup_probes = {"required": unavailable}

    async def enter_lifespan() -> None:
        async with lifecycle.lifespan(app):
            raise AssertionError("required provider failure must prevent serving")

    import asyncio

    with pytest.raises(
        lifecycle.StartupError,
        match="API_REQUIRED_DEPENDENCY_UNAVAILABLE:required",
    ):
        asyncio.run(enter_lifespan())
    assert app.state.api_ready is False


def test_in_process_owned_resources_close_in_reverse_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Close only graph-owned resources in reverse acquisition order."""
    monkeypatch.setattr(
        lifecycle,
        "run_api_migrations",
        lambda _: SimpleNamespace(status="success", data=object()),
    )
    closed: list[str] = []
    graph = build_in_process_api_graph(
        _in_process_providers(),
        owned_resource_closers=(
            lambda: closed.append("first"),
            lambda: closed.append("second"),
        ),
    )
    app = create_api_app(build_api_settings(), in_process_graph=graph)

    async def enter_lifespan() -> None:
        async with lifecycle.lifespan(app):
            assert app.state.api_ready is True

    import asyncio

    asyncio.run(enter_lifespan())
    assert closed == ["second", "first"]


def test_lifespan_closes_data_sessions_before_graph_resources(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Release lifespan-composed Data sessions before graph dependencies."""
    monkeypatch.setattr(
        lifecycle,
        "run_api_migrations",
        lambda _: SimpleNamespace(status="success", data=object()),
    )
    closed: list[str] = []
    monkeypatch.setattr(
        lifecycle,
        "close_data_provider_sessions",
        lambda _: closed.append("data") or SimpleNamespace(status="success"),
    )
    graph = build_in_process_api_graph(
        _in_process_providers(),
        owned_resource_closers=(lambda: closed.append("graph"),),
    )
    app = create_api_app(build_api_settings(), in_process_graph=graph)

    async def enter_lifespan() -> None:
        async with lifecycle.lifespan(app):
            assert app.state.api_ready is True

    import asyncio

    asyncio.run(enter_lifespan())
    assert closed == ["data", "graph"]


def test_dev_auto_login_bypasses_auth_in_dev_mode() -> None:
    """Dev auto-login authenticates requests seamlessly in dev environment."""
    config = build_api_settings(environment="dev", dev_auto_login=True)
    app = create_api_app(config)
    readiness_status, readiness_body = get_json(app, "/api/v1/health/readiness")
    assert readiness_status == 200
    assert readiness_body["status"] == "success"

    me_status, me_body = get_json(app, "/api/v1/auth/me")
    assert me_status == 200
    assert me_body["data"]["user_id"] == "usr_haruquantai"
    assert me_body["data"]["username"] == "haruquantai"


def test_dev_auto_login_forbidden_outside_dev_environment() -> None:
    """Settings validation rejects dev_auto_login in non-dev environments."""
    with pytest.raises(
        ValueError, match="dev_auto_login is allowed only in dev environment"
    ):
        build_api_settings(
            environment="production",
            runtime_profile="research",
            execution_route="none",
            dev_auto_login=True,
        )


def test_dev_auto_login_can_be_disabled_in_dev_mode() -> None:
    """Explicitly disabling dev_auto_login in dev environment enforces 401 checks."""
    config = build_api_settings(environment="dev", dev_auto_login=False)
    app = create_api_app(config)
    status_code, body = get_json(app, "/api/v1/health/readiness")
    assert status_code == 401
    assert body["error"]["code"] == "AUTHENTICATION_REQUIRED"
