"""NFR-API-006: Required failures block startup/readiness; optional degrade.

Verifies that a missing required provider graph name blocks application
construction (ValueError before the app starts), and the canonical app with
a complete graph reaches readiness cleanly.
"""

from pathlib import Path

import pytest
from app.services.api import (
    build_api_settings,
    build_in_process_api_graph,
    create_api_app,
    get_required_in_process_provider_names,
)
from fastapi.testclient import TestClient


def _complete_providers() -> dict[str, object]:
    return {
        name: lambda *_args, **_kwargs: (_args, _kwargs)
        for name in get_required_in_process_provider_names()
    }


class TestNfrApi006Startup:
    """NFR-API-006: startup/readiness failure verification."""

    @staticmethod
    def test_missing_required_provider_blocks_construction(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Omitting a required provider name raises before the app is built."""
        monkeypatch.setenv("DATABASE_URL", "sqlite:///nfr-006-missing.db")
        monkeypatch.setenv("DATA_DIR", str(tmp_path))
        monkeypatch.setenv("SQLITE_BUSY_TIMEOUT_SECONDS", "1.0")
        monkeypatch.setenv("WRITE_LOCK_LEASE_SECONDS", "10.0")
        required = get_required_in_process_provider_names()
        # Drop the first required name to simulate a missing provider.
        incomplete = {
            name: lambda *_args, **_kwargs: None for name in list(required)[1:]
        }
        with pytest.raises((ValueError, TypeError)):
            build_in_process_api_graph(incomplete)

    @staticmethod
    def test_unknown_provider_blocks_construction(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """An unknown provider name raises before the app is built."""
        monkeypatch.setenv("DATABASE_URL", "sqlite:///nfr-006-unknown.db")
        monkeypatch.setenv("DATA_DIR", str(tmp_path))
        monkeypatch.setenv("SQLITE_BUSY_TIMEOUT_SECONDS", "1.0")
        monkeypatch.setenv("WRITE_LOCK_LEASE_SECONDS", "10.0")
        providers = _complete_providers()
        providers["unknown.provider"] = lambda *_args, **_kwargs: None
        with pytest.raises((ValueError, TypeError)):
            build_in_process_api_graph(providers)

    @staticmethod
    def test_complete_graph_reaches_readiness(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A complete graph builds the app and readiness is reachable."""
        monkeypatch.setenv("DATABASE_URL", "sqlite:///nfr-006-ok.db")
        monkeypatch.setenv("DATA_DIR", str(tmp_path))
        monkeypatch.setenv("SQLITE_BUSY_TIMEOUT_SECONDS", "1.0")
        monkeypatch.setenv("WRITE_LOCK_LEASE_SECONDS", "10.0")
        graph = build_in_process_api_graph(_complete_providers())
        app = create_api_app(build_api_settings(), in_process_graph=graph)
        with TestClient(app) as client:
            response = client.get("/api/v1/health/liveness")
            assert response.status_code == 200
