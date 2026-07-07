"""Unit tests for the analytics capability registry and request_id traceability."""

from __future__ import annotations

import pytest
from app.services.analytics.contracts.models import MetricConfig
from app.services.analytics.registry import (
    TOOL_REGISTRY,
    clear_active_requests,
    get_active_requests,
    register_tool,
    request_id,
)
from app.utils.errors import ValidationError


@pytest.fixture(autouse=True)
def _reset_registry_and_active_requests() -> None:
    """Fixture to reset central registries and active requests state per test."""
    clear_active_requests()
    TOOL_REGISTRY.clear()


def test_register_tool_success() -> None:
    """Test successful tool registration via decorator."""

    @register_tool(
        name="test_tool",
        stability="stable",
        safe_for_agent_api=True,
        category="official_tool",
        aliases=("test_tool_alias",),
    )
    def my_dummy_tool(request_id: str) -> str:
        """This is a dummy test tool."""
        return f"result-{request_id}"

    assert "test_tool" in TOOL_REGISTRY
    assert "test_tool_alias" in TOOL_REGISTRY

    entry = TOOL_REGISTRY["test_tool"]
    assert entry.name == "test_tool"
    assert entry.callable_obj == my_dummy_tool
    assert entry.stability == "stable"
    assert entry.safe_for_agent_api is True
    assert entry.category == "official_tool"
    assert "This is a dummy test tool." in entry.description
    assert entry.aliases == ("test_tool_alias",)


def test_register_tool_collision() -> None:
    """Test registering duplicate names or aliases throws ValidationError."""

    @register_tool(
        name="colliding_name",
        stability="approved_experimental",
        safe_for_agent_api=False,
        category="internal_metric_kernel",
    )
    def tool_one() -> None:
        pass

    with pytest.raises(ValidationError) as exc_info:

        @register_tool(
            name="colliding_name",
            stability="stable",
            safe_for_agent_api=True,
            category="official_tool",
        )
        def tool_two() -> None:
            pass

    assert "Duplicate registry name collision" in str(exc_info.value)

    # Check alias collision
    with pytest.raises(ValidationError) as exc_info:

        @register_tool(
            name="another_name",
            stability="stable",
            safe_for_agent_api=True,
            category="official_tool",
            aliases=("colliding_name",),
        )
        def tool_three() -> None:
            pass

    assert "Duplicate registry alias collision" in str(exc_info.value)


def test_request_id_extraction() -> None:
    """Test request_id extraction across different formats."""
    config = MetricConfig()

    # 1. String direct input
    res1 = request_id("REQ123", config)
    assert res1.value == "REQ123"
    assert res1.confidence == "normal"
    assert len(res1.warnings) == 0

    # 2. Dictionary input
    res2 = request_id({"request_id": "REQ456"}, config)
    assert res2.value == "REQ456"
    assert res2.confidence == "normal"
    assert len(res2.warnings) == 0

    # 3. Object attribute input
    class CustomObj:
        def __init__(self, req_id: str):
            self.request_id = req_id

    res3 = request_id(CustomObj("REQ789"), config)
    assert res3.value == "REQ789"
    assert res3.confidence == "normal"

    # 4. Fallback to config attributes
    class SubConfig(MetricConfig):
        request_id: str = "REQ-CONFIG-99"

    res4 = request_id(None, SubConfig())
    assert res4.value == "REQ-CONFIG-99"
    assert res4.confidence == "normal"


def test_request_id_warnings_missing_or_invalid() -> None:
    """Test request_id validation warning flags are emitted appropriately."""
    config = MetricConfig()

    # Missing request id
    res_missing = request_id(None, config)
    assert res_missing.value == "UNKNOWN_REQUEST_ID"
    assert res_missing.confidence == "degraded"
    assert any(w["code"] == "MISSING_REQUEST_ID" for w in res_missing.warnings)

    # Non-string request id
    res_invalid_type = request_id({"request_id": 12345}, config)
    assert res_invalid_type.value == "12345"
    assert res_invalid_type.confidence == "degraded"
    assert any(
        w["code"] == "INVALID_REQUEST_ID_TYPE" for w in res_invalid_type.warnings
    )

    # Unsafe request id characters
    res_unsafe = request_id("REQ_123; DROP TABLE metrics;", config)
    assert res_unsafe.value == "REQ_123; DROP TABLE metrics;"
    assert res_unsafe.confidence == "degraded"
    assert any(w["code"] == "UNSAFE_REQUEST_ID" for w in res_unsafe.warnings)


def test_active_requests_observability() -> None:
    """Test request_id logging triggers state mutation in observability log."""
    config = MetricConfig()
    assert len(get_active_requests()) == 0

    request_id("REQ-A", config)
    request_id("REQ-B", config)

    active = get_active_requests()
    assert "REQ-A" in active
    assert "REQ-B" in active
    assert len(active) == 2

    clear_active_requests()
    assert len(get_active_requests()) == 0
