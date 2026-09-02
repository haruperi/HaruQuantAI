"""Unit tests for ResultPanelsService and FR-PLUG-SANDBOX_RESULT_PANELS."""

from __future__ import annotations

import uuid

import pytest
from app.contracts.plugins.errors import PluginFailure
from app.contracts.plugins.models import (
    PanelBridgeOperation,
    RenderResultPanelsRequest,
    RenderResultPanelsSuccess,
    ResultPanelDescriptor,
)
from app.services.plugins.result_panels.config import ResultPanelsConfig
from app.services.plugins.result_panels.plugin_result_panels import (
    ResultPanelsService,
    _run_usage_example,
    fr_plug_sandbox_result_panels,
)


def _make_sample_panel(
    panel_id: str = "panel.test.sample",
    contribution_id: str = "contrib.test.1",
    bridge_operations: tuple[PanelBridgeOperation, ...] = (
        "READ_RESULTS",
        "QUERY_DATA",
    ),
    content_source: str = "app://plugins/sample/index.html",
) -> ResultPanelDescriptor:
    return ResultPanelDescriptor(
        panel_id=panel_id,
        contribution_id=contribution_id,
        plugin_id="com.haruquantai.test",
        title="Sample Test Panel",
        bridge_operations=bridge_operations,
        content_source=content_source,
    )


@pytest.mark.asyncio
async def test_plug_sandbox_result_panels_describe_success() -> None:
    service = ResultPanelsService()
    p1 = _make_sample_panel("panel.1", "contrib.a")
    p2 = _make_sample_panel("panel.2", "contrib.b")
    service.register_panel(p1)
    service.register_panel(p2)

    req = RenderResultPanelsRequest(
        request_id=str(uuid.uuid7()),
        capability_snapshot_id=str(uuid.uuid7()),
        operation="DESCRIBE_PANELS",
    )
    response = await service.render_result_panels(req)
    assert isinstance(response, RenderResultPanelsSuccess)
    assert len(response.panels) == 2

    # Filter by contribution_id
    filter_req = RenderResultPanelsRequest(
        request_id=str(uuid.uuid7()),
        capability_snapshot_id=str(uuid.uuid7()),
        operation="DESCRIBE_PANELS",
        contribution_id="contrib.a",
    )
    filter_resp = await service.render_result_panels(filter_req)
    assert isinstance(filter_resp, RenderResultPanelsSuccess)
    assert len(filter_resp.panels) == 1
    assert filter_resp.panels[0].panel_id == "panel.1"


@pytest.mark.asyncio
async def test_plug_sandbox_result_panels_resolve_success() -> None:
    service = ResultPanelsService()
    p = _make_sample_panel("panel.target", "contrib.x")
    service.register_panel(p)

    req = RenderResultPanelsRequest(
        request_id=str(uuid.uuid7()),
        capability_snapshot_id=str(uuid.uuid7()),
        operation="RESOLVE_PANEL",
        panel_id="panel.target",
    )
    response = await service.render_result_panels(req)
    assert isinstance(response, RenderResultPanelsSuccess)
    assert len(response.panels) == 1
    assert response.panels[0].panel_id == "panel.target"


@pytest.mark.asyncio
async def test_resolve_not_found_returns_failure() -> None:
    service = ResultPanelsService()
    req = RenderResultPanelsRequest(
        request_id=str(uuid.uuid7()),
        capability_snapshot_id=str(uuid.uuid7()),
        operation="RESOLVE_PANEL",
        panel_id="nonexistent.panel",
    )
    response = await service.render_result_panels(req)
    assert isinstance(response, PluginFailure)
    assert response.code == "PLUGIN_VALIDATION_FAILED"
    assert response.problem.status == 404
    assert "was not found" in response.problem.detail


@pytest.mark.asyncio
async def test_insecure_content_source_rejected() -> None:
    service = ResultPanelsService()
    bad_panel = _make_sample_panel(
        "panel.bad",
        content_source="javascript:evil()",
    )
    service.register_panel(bad_panel)

    req = RenderResultPanelsRequest(
        request_id=str(uuid.uuid7()),
        capability_snapshot_id=str(uuid.uuid7()),
        operation="RESOLVE_PANEL",
        panel_id="panel.bad",
    )
    response = await service.render_result_panels(req)
    assert isinstance(response, PluginFailure)
    assert response.code == "PLUGIN_PERMISSION_DENIED"
    assert response.problem.status == 403
    assert "insecure content source" in response.problem.detail.lower()


@pytest.mark.asyncio
async def test_disallowed_bridge_operations_rejected() -> None:
    cfg = ResultPanelsConfig(allowed_bridge_operations=("READ_RESULTS",))
    service = ResultPanelsService(config=cfg)
    panel = _make_sample_panel(
        "panel.disallowed_bridge",
        bridge_operations=("READ_RESULTS", "RECEIVE_MESSAGES"),
    )
    service.register_panel(panel)

    req = RenderResultPanelsRequest(
        request_id=str(uuid.uuid7()),
        capability_snapshot_id=str(uuid.uuid7()),
        operation="RESOLVE_PANEL",
        panel_id="panel.disallowed_bridge",
    )
    response = await service.render_result_panels(req)
    assert isinstance(response, PluginFailure)
    assert response.code == "PLUGIN_PERMISSION_DENIED"
    assert response.problem.status == 403
    assert "disallowed bridge operations" in response.problem.detail.lower()


@pytest.mark.asyncio
async def test_max_panels_limit_exceeded() -> None:
    cfg = ResultPanelsConfig(max_panels_per_query=2)
    service = ResultPanelsService(config=cfg)
    for i in range(3):
        service.register_panel(_make_sample_panel(f"panel.{i}"))

    req = RenderResultPanelsRequest(
        request_id=str(uuid.uuid7()),
        capability_snapshot_id=str(uuid.uuid7()),
        operation="DESCRIBE_PANELS",
    )
    response = await service.render_result_panels(req)
    assert isinstance(response, PluginFailure)
    assert response.code == "PLUGIN_VALIDATION_FAILED"
    assert response.problem.status == 400
    assert "exceeds limit" in response.problem.detail


def test_trace_function_fr_plug_sandbox_result_panels() -> None:
    service = ResultPanelsService()
    p = _make_sample_panel("panel.trace")
    service.register_panel(p)

    req = RenderResultPanelsRequest(
        request_id=str(uuid.uuid7()),
        capability_snapshot_id=str(uuid.uuid7()),
        operation="RESOLVE_PANEL",
        panel_id="panel.trace",
    )
    response = fr_plug_sandbox_result_panels(req, service=service)
    assert isinstance(response, RenderResultPanelsSuccess)
    assert len(response.panels) == 1


def test_service_crud_and_clear() -> None:
    service = ResultPanelsService()
    p = _make_sample_panel("panel.crud")
    service.register_panel(p)
    assert service.get_panel("panel.crud") is p
    assert service.unregister_panel("panel.crud") is True
    assert service.get_panel("panel.crud") is None
    assert service.unregister_panel("panel.crud") is False

    service.register_panel(p)
    service.clear()
    assert len(service.list_panels()) == 0


def test_run_usage_example() -> None:
    _run_usage_example()
