"""Unit tests for SessionCalendarFeature lifecycle and entry points."""

from unittest.mock import MagicMock

import pytest
from app.contracts.catalogue.capabilities import DEFINE_SESSIONS_CAPABILITY
from app.kernel.context import FeatureContext
from app.services.catalogue.session_calendar.feature import (
    SessionCalendarFeature,
    feature,
)
from app.services.catalogue.session_calendar.manifest import SPEC


def test_session_calendar_feature_instantiation() -> None:
    """Verify feature factory and spec bindings."""
    feat = feature()
    assert isinstance(feat, SessionCalendarFeature)
    assert feat.spec == SPEC
    assert feat.spec.feature_id == "FEAT-CAT-DEFINE_SESSIONS"
    assert DEFINE_SESSIONS_CAPABILITY in feat.spec.provides


@pytest.mark.asyncio
async def test_session_calendar_feature_mount_dict() -> None:
    """Verify mounting feature with dictionary config."""
    feat = feature()
    context = MagicMock(spec=FeatureContext)
    await feat.mount(context, {"database_path": None, "auto_migrate": True})
    assert feat.service is not None
    context.provide.assert_called_once_with(DEFINE_SESSIONS_CAPABILITY, feat.service)


@pytest.mark.asyncio
async def test_session_calendar_feature_mount_invalid_config() -> None:
    """Verify mounting feature with invalid config raises TypeError."""
    feat = feature()
    context = MagicMock(spec=FeatureContext)
    with pytest.raises(TypeError, match="database_path must be a string"):
        await feat.mount(context, {"database_path": 12345})
