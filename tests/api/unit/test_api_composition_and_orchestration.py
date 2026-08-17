"""Unit tests for API composition and orchestration components."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from app.services.api.composition.broker_session import (
    create_non_production_broker_session,
)
from app.services.api.composition.owner_sources import (
    read_dashboard_snapshot,
)
from app.services.api.composition.runtime_settings import (
    build_credential_key_set,
)


def test_api_composition_broker_session_production_guard() -> None:
    """Verify create_non_production_broker_session rejects live/production environments."""
    import asyncio

    with pytest.raises(ValueError, match="production broker environments are excluded"):
        asyncio.run(
            create_non_production_broker_session(
                credential_reference="cred-1",
                owner_id="owner-1",
                key_set={},
                request_id="req-1",
                broker_id="mt5",
                environment="live",
            )
        )


def test_api_composition_owner_sources_dashboard() -> None:
    """Verify read_dashboard_snapshot routing and error handling."""
    auth = MagicMock()
    with pytest.raises(ValueError, match="unsupported dashboard view"):
        read_dashboard_snapshot("invalid_dashboard_name", auth)


def test_api_composition_runtime_settings_key_set() -> None:
    """Verify build_credential_key_set with unprovisioned settings."""
    settings = MagicMock()
    settings.credential_encryption_key = None
    key_set = build_credential_key_set(settings)
    assert len(key_set) == 0
