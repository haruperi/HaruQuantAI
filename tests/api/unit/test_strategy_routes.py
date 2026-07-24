"""Authenticated Strategy route tests."""

from contextlib import AbstractContextManager
from pathlib import Path

from app.services.api.identity import require_auth_context
from app.services.api.routes import strategies
from app.services.api.routes.strategies import router
from app.services.data import DataSettings, data_settings_context
from fastapi import FastAPI

from tests.api._support import post_json
from tests.strategy.unit.test_catalog import make_registration
from tests.strategy.unit.test_models import make_auth, make_policy


def _storage(root: Path) -> AbstractContextManager[None]:
    """Build isolated Strategy persistence settings.

    Args:
        root: Temporary Data root.

    Returns:
        Data settings context manager.
    """
    return data_settings_context(
        DataSettings(
            database_url="sqlite:///api-strategy.sqlite3",
            data_dir=root,
            sqlite_busy_timeout_seconds=1.5,
            write_lock_lease_seconds=30,
        )
    )


def _app() -> FastAPI:
    """Build an authenticated Strategy API application.

    Returns:
        Configured FastAPI application.
    """
    app = FastAPI()
    app.include_router(router)
    auth = make_auth()
    app.dependency_overrides[require_auth_context] = lambda: auth
    app.dependency_overrides[strategies._strategy_validation_policy] = make_policy
    return app


def test_strategy_registration_delegates_to_owner(tmp_path: Path) -> None:
    """Verify authenticated route returns Strategy mutation truth."""
    request = make_registration()

    with _storage(tmp_path):
        status_code, body = post_json(
            _app(),
            "/api/strategies/registrations",
            request.model_dump(mode="json"),
        )

    assert status_code == 200, body
    assert body["status"] == "ACCEPTED"
    assert body["strategy_id"] == request.strategy_id


def test_strategy_registration_rejects_principal_mismatch(tmp_path: Path) -> None:
    """Verify API cannot submit a command for another principal."""
    request = make_registration().model_copy(update={"principal_id": "other"})

    with _storage(tmp_path):
        status_code, body = post_json(
            _app(),
            "/api/strategies/registrations",
            request.model_dump(mode="json"),
        )

    assert status_code == 403
    assert body["detail"] == "PRINCIPAL_MISMATCH"
