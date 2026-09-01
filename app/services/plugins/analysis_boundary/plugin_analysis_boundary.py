"""Primary service for isolating plugin analysis inputs and staged outputs.

Purpose:
    Constrain plugin analysis inputs and staged outputs per ?21.4.

Key capabilities:
    * Receive immutable read-only input artifact handles.
    * Enforce size bounds on parameters and handle limits.
    * Produce schema-validated staged output without direct database mutation.
    * Provide async isolate_analysis implementing IsolateAnalysisCapability.

Python API usage:
    from app.services.plugins.analysis_boundary.plugin_analysis_boundary import (
        IsolateAnalysisService,
    )
    service = IsolateAnalysisService()
    result = await service.isolate_analysis(request)

CLI usage:
    uv run python -m app.services.plugins.analysis_boundary.plugin_analysis_boundary
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from collections.abc import Callable
from typing import TYPE_CHECKING, override

from app.contracts.common.models import ProblemDetails, Uuid7, ValidationIssue
from app.contracts.plugins.errors import PluginFailure, PluginFailureCode
from app.contracts.plugins.models import (
    IsolateAnalysisRequest,
    IsolateAnalysisSuccess,
    PluginAnalysisRequest,
    PluginAnalysisResult,
    PluginInputHandle,
)
from app.contracts.plugins.ports import IsolateAnalysisCapability
from app.services.plugins.analysis_boundary.config import IsolateAnalysisConfig

if TYPE_CHECKING:
    from app.contracts.plugins.ports import SandboxPermissionsCapability

logger = logging.getLogger(__name__)


def _make_failure(
    request_id: Uuid7,
    code: PluginFailureCode,
    status: int,
    title: str,
    detail: str,
    *,
    errors: tuple[ValidationIssue, ...] = (),
) -> PluginFailure:
    """Construct a standard PluginFailure envelope with ProblemDetails.

    Args:
        request_id: Request UUID identifier.
        code: Machine-readable failure code.
        status: HTTP status code.
        title: Short human-readable summary.
        detail: Detailed explanation of the failure.
        errors: Optional tuple of validation issues.

    Returns:
        Populated PluginFailure model instance.
    """
    error_slug = code.lower().replace("_", "-")
    return PluginFailure(
        request_id=request_id,
        code=code,
        problem=ProblemDetails(
            type=f"urn:haruquantai:plugins:{error_slug}",
            title=title,
            status=status,
            code=code,
            detail=detail,
            request_id=request_id,
            errors=errors,
        ),
    )


class IsolateAnalysisService(IsolateAnalysisCapability):
    """Domain service implementing the IsolateAnalysisCapability protocol.

    Provides input handle immutability enforcement, parameter payload bounds,
    and schema-validated staged output generation.
    """

    def __init__(
        self,
        config: IsolateAnalysisConfig | None = None,
        sandbox: SandboxPermissionsCapability | None = None,
    ) -> None:
        """Initialize the analysis boundary service.

        Args:
            config: Optional configuration settings.
            sandbox: Optional SandboxPermissionsCapability provider.
        """
        self._config = config or IsolateAnalysisConfig()
        self._sandbox = sandbox
        self._custom_handlers: dict[
            str, Callable[[PluginAnalysisRequest], PluginAnalysisResult]
        ] = {}

    def register_handler(
        self,
        contribution_id: str,
        handler: Callable[[PluginAnalysisRequest], PluginAnalysisResult],
    ) -> None:
        """Register a custom analysis handler for testing or custom execution.

        Args:
            contribution_id: Contribution identifier.
            handler: Callable taking request and returning PluginAnalysisResult.
        """
        self._custom_handlers[contribution_id] = handler

    def unregister_handler(self, contribution_id: str) -> None:
        """Unregister a custom analysis handler.

        Args:
            contribution_id: Contribution identifier.
        """
        self._custom_handlers.pop(contribution_id, None)

    def clear(self) -> None:
        """Clear registered handlers and state on unmount or feature removal."""
        self._custom_handlers.clear()

    @override
    async def isolate_analysis(
        self,
        request: IsolateAnalysisRequest,
    ) -> IsolateAnalysisSuccess | PluginFailure:
        """Run one plugin analysis with immutable handles and staged output.

        Args:
            request: Operation-discriminated plugin analysis boundary request.

        Returns:
            The staged analysis result on success, or structured failure.
        """
        analysis = request.analysis

        # 1. Enforce max input handles
        if len(analysis.input_handles) > self._config.max_input_handles:
            detail = (
                f"Number of input handles ({len(analysis.input_handles)}) "
                f"exceeds maximum allowed limit ({self._config.max_input_handles})"
            )
            issue_msg = f"Input handles count exceeds {self._config.max_input_handles}"
            return _make_failure(
                request_id=request.request_id,
                code="PLUGIN_VALIDATION_FAILED",
                status=400,
                title="Input Handles Limit Exceeded",
                detail=detail,
                errors=(
                    ValidationIssue(
                        path=("analysis", "input_handles"),
                        code="MAX_LIMIT_EXCEEDED",
                        message=issue_msg,
                    ),
                ),
            )

        # 2. Verify all handles are read_only
        for idx, handle in enumerate(analysis.input_handles):
            if getattr(handle, "read_only", None) is not True:
                return _make_failure(
                    request_id=request.request_id,
                    code="PLUGIN_PERMISSION_DENIED",
                    status=403,
                    title="Mutable Input Handle Rejected",
                    detail="Plugin analysis inputs must be strictly read-only",
                    errors=(
                        ValidationIssue(
                            path=("analysis", "input_handles", str(idx)),
                            code="HANDLE_NOT_READ_ONLY",
                            message="Input handle must have read_only=True",
                        ),
                    ),
                )

        # 3. Enforce max parameter payload bytes
        try:
            param_str = json.dumps(analysis.parameters)
            param_bytes = len(param_str.encode("utf-8"))
        except (TypeError, ValueError) as json_err:
            detail = f"Parameters payload could not be serialized to JSON: {json_err}"
            return _make_failure(
                request_id=request.request_id,
                code="PLUGIN_VALIDATION_FAILED",
                status=400,
                title="Invalid Parameters JSON",
                detail=detail,
            )

        if param_bytes > self._config.max_parameter_bytes:
            detail = (
                f"Parameter payload size ({param_bytes} bytes) exceeds "
                f"maximum allowed bytes ({self._config.max_parameter_bytes})"
            )
            issue_msg = (
                f"Parameters byte size {param_bytes} exceeds "
                f"{self._config.max_parameter_bytes}"
            )
            return _make_failure(
                request_id=request.request_id,
                code="PLUGIN_VALIDATION_FAILED",
                status=400,
                title="Parameter Payload Size Exceeded",
                detail=detail,
                errors=(
                    ValidationIssue(
                        path=("analysis", "parameters"),
                        code="PAYLOAD_TOO_LARGE",
                        message=issue_msg,
                    ),
                ),
            )

        # 4. Execute analysis
        try:
            if analysis.contribution_id in self._custom_handlers:
                result = self._custom_handlers[analysis.contribution_id](analysis)
            else:
                # Default evaluation: create a schema-validated staged output
                staged_id = str(uuid.uuid7())
                result = PluginAnalysisResult(
                    request_id=analysis.request_id,
                    contribution_id=analysis.contribution_id,
                    status="SUCCEEDED",
                    staged_artifact_id=staged_id,
                    errors=(),
                )

            # 5. Output schema enforcement
            if (
                self._config.enforce_staged_output_schema
                and result.status == "SUCCEEDED"
                and result.staged_artifact_id is None
            ):
                result = PluginAnalysisResult(
                    request_id=analysis.request_id,
                    contribution_id=analysis.contribution_id,
                    status="FAILED",
                    staged_artifact_id=None,
                    errors=(
                        ValidationIssue(
                            path=("result", "staged_artifact_id"),
                            code="STAGED_ARTIFACT_MISSING",
                            message="Successful analysis must have staged artifact ID",
                        ),
                    ),
                )

            return IsolateAnalysisSuccess(
                request_id=request.request_id,
                result=result,
            )

        except Exception as exc:
            logger.exception("Error executing plugin analysis")
            detail = (
                f"Execution of contribution {analysis.contribution_id} failed: {exc}"
            )
            return _make_failure(
                request_id=request.request_id,
                code="PLUGIN_SANDBOX_EXECUTION_FAILED",
                status=500,
                title="Plugin Analysis Execution Failed",
                detail=detail,
            )


def fr_plug_pass_artifact_handles(
    request: IsolateAnalysisRequest,
    service: IsolateAnalysisService | None = None,
    config: IsolateAnalysisConfig | None = None,
) -> IsolateAnalysisSuccess | PluginFailure:
    """Requirement implementation trace for FR-PLUG-PASS_ARTIFACT_HANDLES.

    Args:
        request: IsolateAnalysisRequest instance.
        service: Optional IsolateAnalysisService instance.
        config: Optional configuration limits.

    Returns:
        IsolateAnalysisSuccess or PluginFailure outcome.
    """
    svc = service or IsolateAnalysisService(config=config)
    return asyncio.run(svc.isolate_analysis(request))


def _run_usage_example() -> None:
    """Execute the bounded public usage demonstration and verification harness.

    Raises:
        RuntimeError: If verification assertion fails.
        TypeError: If response type check fails.
    """
    print("=== Demonstrating FR-PLUG-PASS_ARTIFACT_HANDLES Usage ===")
    service = IsolateAnalysisService()

    req_id = str(uuid.uuid7())
    snapshot_id = str(uuid.uuid7())
    artifact_id_1 = str(uuid.uuid7())
    artifact_id_2 = str(uuid.uuid7())

    handle1 = PluginInputHandle(
        artifact_id=artifact_id_1,
        content_hash="a" * 64,
        media_type="application/x-parquet",
        read_only=True,
    )
    handle2 = PluginInputHandle(
        artifact_id=artifact_id_2,
        content_hash="b" * 64,
        media_type="application/json",
        read_only=True,
    )

    analysis_req = PluginAnalysisRequest(
        request_id=req_id,
        plugin_id="com.haruquantai.sample.analytics",
        contribution_id="com.haruquantai.sample.analytics.rsi",
        input_handles=(handle1, handle2),
        parameters={"lookback": 14, "mode": "exponential"},
    )

    request = IsolateAnalysisRequest(
        request_id=req_id,
        capability_snapshot_id=snapshot_id,
        operation="ANALYZE",
        analysis=analysis_req,
    )

    # 1. Execute analysis through the boundary
    response = asyncio.run(service.isolate_analysis(request))
    if not isinstance(response, IsolateAnalysisSuccess) or response.result is None:
        err_msg = f"Expected IsolateAnalysisSuccess, got {response}"
        raise TypeError(err_msg)

    print(
        f"1. Successfully executed isolated analysis for {analysis_req.contribution_id}"
    )
    print(f"   Status: {response.result.status}")
    print(f"   Staged Artifact ID: {response.result.staged_artifact_id}")

    # 2. Verify trace function
    trace_res = fr_plug_pass_artifact_handles(request, service=service)
    if not isinstance(trace_res, IsolateAnalysisSuccess):
        err_msg = "fr_plug_pass_artifact_handles failed"
        raise TypeError(err_msg)
    print("2. Trace function fr_plug_pass_artifact_handles verified.")

    # 3. Verify handle limit enforcement
    over_limit_handles = tuple(
        PluginInputHandle(
            artifact_id=str(uuid.uuid7()),
            content_hash="c" * 64,
            media_type="application/octet-stream",
            read_only=True,
        )
        for _ in range(60)
    )
    over_limit_req = IsolateAnalysisRequest(
        request_id=str(uuid.uuid7()),
        capability_snapshot_id=snapshot_id,
        operation="ANALYZE",
        analysis=PluginAnalysisRequest(
            request_id=str(uuid.uuid7()),
            plugin_id="com.haruquantai.sample.analytics",
            contribution_id="com.haruquantai.sample.analytics.rsi",
            input_handles=over_limit_handles,
            parameters={},
        ),
    )
    limit_resp = asyncio.run(service.isolate_analysis(over_limit_req))
    if (
        not isinstance(limit_resp, PluginFailure)
        or limit_resp.code != "PLUGIN_VALIDATION_FAILED"
    ):
        err_msg = "Expected handle limit failure"
        raise RuntimeError(err_msg)
    print(f"3. Verified handle limit failure: {limit_resp.problem.detail}")

    print("=== Usage demonstration completed successfully ===")


if __name__ == "__main__":
    _run_usage_example()
