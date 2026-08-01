"""Standalone canonical application lifecycle usage."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.api import (
    build_api_settings,
    build_in_process_api_graph,
    create_api_app,
    get_required_in_process_provider_names,
)
from fastapi.testclient import TestClient


def main() -> None:
    """Start the canonical app with isolated required storage."""
    variable_names = (
        "DATABASE_URL",
        "DATA_DIR",
        "SQLITE_BUSY_TIMEOUT_SECONDS",
        "WRITE_LOCK_LEASE_SECONDS",
    )
    with TemporaryDirectory() as directory:
        previous = {name: os.environ.get(name) for name in variable_names}
        os.environ.update(
            {
                "DATABASE_URL": "sqlite:///api-composition-usage.db",
                "DATA_DIR": directory,
                "SQLITE_BUSY_TIMEOUT_SECONDS": "1.0",
                "WRITE_LOCK_LEASE_SECONDS": "10.0",
            }
        )
        try:
            providers: dict[str, object] = {
                name: lambda *args, **kwargs: (args, kwargs)
                for name in get_required_in_process_provider_names()
            }
            graph = build_in_process_api_graph(providers)
            application = create_api_app(
                build_api_settings(ui_origins=("http://localhost:3000",)),
                in_process_graph=graph,
            )
            with TestClient(application) as client:
                response = client.get("/api/v1/health/liveness")
                assert response.status_code == 200
                assert application.state.api_ready is True
            assert application.state.api_ready is False
            print({"liveness": "passed", "lifecycle": "closed"})
        finally:
            for name, value in previous.items():
                if value is None:
                    os.environ.pop(name, None)
                else:
                    os.environ[name] = value


if __name__ == "__main__":
    main()
