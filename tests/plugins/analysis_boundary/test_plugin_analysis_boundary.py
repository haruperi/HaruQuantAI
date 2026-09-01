"""Unit tests for IsolateAnalysisService and FR-PLUG-PASS_ARTIFACT_HANDLES."""

from __future__ import annotations

import uuid

import pytest
from app.contracts.common.models import JsonValue, ValidationIssue
from app.contracts.plugins.errors import PluginFailure
from app.contracts.plugins.models import (
    IsolateAnalysisRequest,
    IsolateAnalysisSuccess,
    PluginAnalysisRequest,
    PluginAnalysisResult,
    PluginInputHandle,
)
from app.services.plugins.analysis_boundary.config import IsolateAnalysisConfig
from app.services.plugins.analysis_boundary.plugin_analysis_boundary import (
    IsolateAnalysisService,
    _run_usage_example,
    fr_plug_pass_artifact_handles,
)


def _make_sample_request(
    num_handles: int = 1,
    parameters: dict[str, JsonValue] | None = None,
) -> IsolateAnalysisRequest:
    req_id = str(uuid.uuid7())
    snapshot_id = str(uuid.uuid7())
    handles = tuple(
        PluginInputHandle(
            artifact_id=str(uuid.uuid7()),
            content_hash="a" * 64,
            media_type="application/json",
            read_only=True,
        )
        for _ in range(num_handles)
    )
    analysis = PluginAnalysisRequest(
        request_id=req_id,
        plugin_id="com.haruquantai.test.plugin",
        contribution_id="com.haruquantai.test.plugin.analysis1",
        input_handles=handles,
        parameters=parameters or {"window": 20},
    )
    return IsolateAnalysisRequest(
        request_id=req_id,
        capability_snapshot_id=snapshot_id,
        operation="ANALYZE",
        analysis=analysis,
    )


@pytest.mark.asyncio
async def test_plug_pass_artifact_handles_success() -> None:
    service = IsolateAnalysisService()
    req = _make_sample_request(num_handles=2)
    response = await service.isolate_analysis(req)

    assert isinstance(response, IsolateAnalysisSuccess)
    assert response.request_id == req.request_id
    assert response.result is not None
    assert response.result.status == "SUCCEEDED"
    assert response.result.staged_artifact_id is not None
    assert response.result.contribution_id == req.analysis.contribution_id
    assert len(response.result.errors) == 0


@pytest.mark.asyncio
async def test_custom_handler_and_error_reporting() -> None:
    service = IsolateAnalysisService()
    contribution_id = "com.haruquantai.test.plugin.custom"

    def fail_handler(analysis: PluginAnalysisRequest) -> PluginAnalysisResult:
        return PluginAnalysisResult(
            request_id=analysis.request_id,
            contribution_id=analysis.contribution_id,
            status="FAILED",
            staged_artifact_id=None,
            errors=(
                ValidationIssue(
                    path=("custom",),
                    code="CALCULATION_FAILED",
                    message="Division by zero in formula",
                ),
            ),
        )

    service.register_handler(contribution_id, fail_handler)

    req = _make_sample_request()
    req = IsolateAnalysisRequest(
        request_id=req.request_id,
        capability_snapshot_id=req.capability_snapshot_id,
        operation="ANALYZE",
        analysis=PluginAnalysisRequest(
            request_id=req.analysis.request_id,
            plugin_id=req.analysis.plugin_id,
            contribution_id=contribution_id,
            input_handles=req.analysis.input_handles,
            parameters={},
        ),
    )

    response = await service.isolate_analysis(req)
    assert isinstance(response, IsolateAnalysisSuccess)
    assert response.result is not None
    assert response.result.status == "FAILED"
    assert response.result.staged_artifact_id is None
    assert len(response.result.errors) == 1
    assert response.result.errors[0].code == "CALCULATION_FAILED"

    # Unregister handler
    service.unregister_handler(contribution_id)
    response2 = await service.isolate_analysis(req)
    assert isinstance(response2, IsolateAnalysisSuccess)
    assert response2.result is not None
    assert response2.result.status == "SUCCEEDED"


@pytest.mark.asyncio
async def test_enforce_schema_failure_when_staged_id_missing() -> None:
    cfg = IsolateAnalysisConfig(enforce_staged_output_schema=True)
    service = IsolateAnalysisService(config=cfg)
    contribution_id = "com.haruquantai.test.plugin.missing_staged"

    def bad_handler(analysis: PluginAnalysisRequest) -> PluginAnalysisResult:
        return PluginAnalysisResult(
            request_id=analysis.request_id,
            contribution_id=analysis.contribution_id,
            status="SUCCEEDED",
            staged_artifact_id=None,
            errors=(),
        )

    service.register_handler(contribution_id, bad_handler)
    req = _make_sample_request()
    req = IsolateAnalysisRequest(
        request_id=req.request_id,
        capability_snapshot_id=req.capability_snapshot_id,
        operation="ANALYZE",
        analysis=PluginAnalysisRequest(
            request_id=req.analysis.request_id,
            plugin_id=req.analysis.plugin_id,
            contribution_id=contribution_id,
            input_handles=req.analysis.input_handles,
            parameters={},
        ),
    )

    response = await service.isolate_analysis(req)
    assert isinstance(response, IsolateAnalysisSuccess)
    assert response.result is not None
    assert response.result.status == "FAILED"
    assert len(response.result.errors) == 1
    assert response.result.errors[0].code == "STAGED_ARTIFACT_MISSING"


@pytest.mark.asyncio
async def test_input_handles_limit_exceeded() -> None:
    config = IsolateAnalysisConfig(max_input_handles=3)
    service = IsolateAnalysisService(config=config)
    req = _make_sample_request(num_handles=4)

    response = await service.isolate_analysis(req)
    assert isinstance(response, PluginFailure)
    assert response.code == "PLUGIN_VALIDATION_FAILED"
    assert response.problem.status == 400
    assert "exceeds maximum allowed limit" in response.problem.detail


@pytest.mark.asyncio
async def test_parameters_payload_size_exceeded() -> None:
    config = IsolateAnalysisConfig(max_parameter_bytes=300)
    service = IsolateAnalysisService(config=config)
    large_params: dict[str, JsonValue] = {"data": "x" * 500}
    req = _make_sample_request(parameters=large_params)

    response = await service.isolate_analysis(req)
    assert isinstance(response, PluginFailure)
    assert response.code == "PLUGIN_VALIDATION_FAILED"
    assert response.problem.status == 400
    assert "exceeds maximum allowed bytes" in response.problem.detail


@pytest.mark.asyncio
async def test_exception_in_handler_returns_failure() -> None:
    service = IsolateAnalysisService()
    contribution_id = "com.haruquantai.test.plugin.crash"

    def crashing_handler(_analysis: PluginAnalysisRequest) -> PluginAnalysisResult:
        raise RuntimeError("Unexpected fatal crash in worker")

    service.register_handler(contribution_id, crashing_handler)
    req = _make_sample_request()
    req = IsolateAnalysisRequest(
        request_id=req.request_id,
        capability_snapshot_id=req.capability_snapshot_id,
        operation="ANALYZE",
        analysis=PluginAnalysisRequest(
            request_id=req.analysis.request_id,
            plugin_id=req.analysis.plugin_id,
            contribution_id=contribution_id,
            input_handles=req.analysis.input_handles,
            parameters={},
        ),
    )

    response = await service.isolate_analysis(req)
    assert isinstance(response, PluginFailure)
    assert response.code == "PLUGIN_SANDBOX_EXECUTION_FAILED"
    assert response.problem.status == 500


def test_trace_function_fr_plug_pass_artifact_handles() -> None:
    req = _make_sample_request(num_handles=1)
    response = fr_plug_pass_artifact_handles(req)
    assert isinstance(response, IsolateAnalysisSuccess)
    assert response.result is not None
    assert response.result.status == "SUCCEEDED"


def test_run_usage_example() -> None:
    _run_usage_example()
