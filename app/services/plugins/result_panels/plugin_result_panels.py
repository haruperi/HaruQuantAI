"""Primary service for sandboxed plugin result panels.

Purpose:
    Isolate result-panel frontend bundles behind a narrow read-only bridge.

Key capabilities:
    * Register and query wire-native ResultPanelDescriptor models.
    * Enforce sandboxed browser boundary with restricted bridge operations.
    * Block dangerous URI schemes, credentials, and undeclared navigation/commands.
    * Provide async render_result_panels implementing RenderResultPanelsCapability.

Python API usage:
    from app.services.plugins.result_panels.plugin_result_panels import (
        ResultPanelsService,
    )
    service = ResultPanelsService()
    result = await service.render_result_panels(request)

CLI usage:
    uv run python -m app.services.plugins.result_panels.plugin_result_panels
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import TYPE_CHECKING, override

from app.contracts.common.models import ProblemDetails, Uuid7, ValidationIssue
from app.contracts.plugins.errors import PluginFailure, PluginFailureCode
from app.contracts.plugins.models import (
    RenderResultPanelsRequest,
    RenderResultPanelsSuccess,
    ResultPanelDescriptor,
)
from app.contracts.plugins.ports import RenderResultPanelsCapability
from app.services.plugins.result_panels.config import ResultPanelsConfig

if TYPE_CHECKING:
    from app.contracts.plugins.ports import RegisterContributionsCapability

logger = logging.getLogger(__name__)

_DISALLOWED_SCHEMES: tuple[str, ...] = (
    "javascript:",
    "vbscript:",
    "data:text/html",
    "file:",
)


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


def _is_secure_content_source(source: str) -> bool:
    """Validate that a content source URI is safe for sandboxed execution.

    Args:
        source: Content source string or URL.

    Returns:
        True if the content source is safe, False otherwise.
    """
    cleaned = source.strip().lower()
    if not cleaned:
        return False
    for disallowed in _DISALLOWED_SCHEMES:
        if cleaned.startswith(disallowed):
            return False
    if "://" in cleaned:
        scheme_part, rest = cleaned.split("://", 1)
        if "@" in rest.split("/")[0]:
            return False
        if scheme_part not in ("https", "http", "app", "blob", "asset"):
            return False
    return True


class ResultPanelsService(RenderResultPanelsCapability):
    """Domain service implementing the RenderResultPanelsCapability protocol.

    Maintains registered result panel descriptors and resolves panel requests
    with sandboxed boundary constraints.
    """

    def __init__(
        self,
        config: ResultPanelsConfig | None = None,
        contributions_service: RegisterContributionsCapability | None = None,
    ) -> None:
        """Initialize the result panels service.

        Args:
            config: Optional configuration settings.
            contributions_service: Optional RegisterContributionsCapability provider.
        """
        self._config = config or ResultPanelsConfig()
        self._contributions = contributions_service
        self._panels: dict[str, ResultPanelDescriptor] = {}

    def register_panel(self, panel: ResultPanelDescriptor) -> None:
        """Register a sandboxed result panel descriptor in memory.

        Args:
            panel: ResultPanelDescriptor instance.
        """
        self._panels[panel.panel_id] = panel

    def unregister_panel(self, panel_id: str) -> bool:
        """Unregister a panel descriptor by its panel ID.

        Args:
            panel_id: Panel identifier to remove.

        Returns:
            True if removed, False if not found.
        """
        return self._panels.pop(panel_id, None) is not None

    def get_panel(self, panel_id: str) -> ResultPanelDescriptor | None:
        """Retrieve a registered panel descriptor by ID.

        Args:
            panel_id: Panel identifier.

        Returns:
            ResultPanelDescriptor if found, None otherwise.
        """
        return self._panels.get(panel_id)

    def list_panels(
        self, contribution_id: str | None = None
    ) -> tuple[ResultPanelDescriptor, ...]:
        """List registered panel descriptors, optionally filtered by contribution ID.

        Args:
            contribution_id: Optional contribution identifier filter.

        Returns:
            Tuple of matching ResultPanelDescriptor items.
        """
        if contribution_id is None:
            return tuple(self._panels.values())
        return tuple(
            p for p in self._panels.values() if p.contribution_id == contribution_id
        )

    def clear(self) -> None:
        """Clear all registered panels on unmount or feature removal."""
        self._panels.clear()

    def _describe_panels(
        self, request: RenderResultPanelsRequest
    ) -> RenderResultPanelsSuccess | PluginFailure:
        """Handle DESCRIBE_PANELS operation.

        Args:
            request: RenderResultPanelsRequest instance.

        Returns:
            RenderResultPanelsSuccess with valid descriptors or PluginFailure.
        """
        matching = self.list_panels(request.contribution_id)
        if len(matching) > self._config.max_panels_per_query:
            limit = self._config.max_panels_per_query
            detail = f"Matching panels count ({len(matching)}) exceeds limit ({limit})"
            return _make_failure(
                request_id=request.request_id,
                code="PLUGIN_VALIDATION_FAILED",
                status=400,
                title="Panel Query Limit Exceeded",
                detail=detail,
                errors=(
                    ValidationIssue(
                        path=("panels",),
                        code="MAX_LIMIT_EXCEEDED",
                        message=detail,
                    ),
                ),
            )

        valid_panels: list[ResultPanelDescriptor] = []
        for panel in matching:
            if (
                self._config.enforce_secure_content_source
                and not _is_secure_content_source(panel.content_source)
            ):
                logger.warning(
                    "Skipping panel '%s' with insecure content_source: %s",
                    panel.panel_id,
                    panel.content_source,
                )
                continue

            invalid_ops = [
                op
                for op in panel.bridge_operations
                if op not in self._config.allowed_bridge_operations
            ]
            if invalid_ops:
                logger.warning(
                    "Skipping panel '%s' with disallowed bridge operations: %s",
                    panel.panel_id,
                    invalid_ops,
                )
                continue

            valid_panels.append(panel)

        return RenderResultPanelsSuccess(
            request_id=request.request_id,
            panels=tuple(valid_panels),
        )

    def _resolve_panel(
        self, request: RenderResultPanelsRequest
    ) -> RenderResultPanelsSuccess | PluginFailure:
        """Handle RESOLVE_PANEL operation.

        Args:
            request: RenderResultPanelsRequest instance.

        Returns:
            RenderResultPanelsSuccess with resolved panel or PluginFailure.
        """
        panel_id = request.panel_id
        if panel_id is None:
            return _make_failure(
                request_id=request.request_id,
                code="PLUGIN_VALIDATION_FAILED",
                status=400,
                title="Missing Panel ID",
                detail="panel_id is required for RESOLVE_PANEL",
            )

        panel = self.get_panel(panel_id)
        if panel is None:
            detail = f"Result panel with ID '{panel_id}' was not found"
            return _make_failure(
                request_id=request.request_id,
                code="PLUGIN_VALIDATION_FAILED",
                status=404,
                title="Result Panel Not Found",
                detail=detail,
                errors=(
                    ValidationIssue(
                        path=("panel_id",),
                        code="NOT_FOUND",
                        message=detail,
                    ),
                ),
            )

        if self._config.enforce_secure_content_source and not _is_secure_content_source(
            panel.content_source
        ):
            detail = (
                f"Result panel '{panel_id}' has insecure content "
                f"source: {panel.content_source}"
            )
            return _make_failure(
                request_id=request.request_id,
                code="PLUGIN_PERMISSION_DENIED",
                status=403,
                title="Insecure Content Source Rejected",
                detail=detail,
                errors=(
                    ValidationIssue(
                        path=("content_source",),
                        code="INSECURE_CONTENT_SOURCE",
                        message=detail,
                    ),
                ),
            )

        invalid_ops = [
            op
            for op in panel.bridge_operations
            if op not in self._config.allowed_bridge_operations
        ]
        if invalid_ops:
            detail = (
                f"Result panel '{panel_id}' requests undeclared or "
                f"disallowed bridge operations: {invalid_ops}"
            )
            return _make_failure(
                request_id=request.request_id,
                code="PLUGIN_PERMISSION_DENIED",
                status=403,
                title="Disallowed Bridge Operations",
                detail=detail,
                errors=(
                    ValidationIssue(
                        path=("bridge_operations",),
                        code="DISALLOWED_OPERATION",
                        message=detail,
                    ),
                ),
            )

        return RenderResultPanelsSuccess(
            request_id=request.request_id,
            panels=(panel,),
        )

    @override
    async def render_result_panels(
        self,
        request: RenderResultPanelsRequest,
    ) -> RenderResultPanelsSuccess | PluginFailure:
        """Describe or resolve sandboxed plugin result panels.

        Args:
            request: Operation-discriminated plugin result panel request.

        Returns:
            The matching panel descriptors on success, otherwise a
            structured plugins failure.
        """
        try:
            match request.operation:
                case "DESCRIBE_PANELS":
                    return self._describe_panels(request)
                case "RESOLVE_PANEL":
                    return self._resolve_panel(request)

        except Exception as exc:
            logger.exception("Error executing render_result_panels")
            detail = f"Failed to execute render_result_panels: {exc}"
            return _make_failure(
                request_id=request.request_id,
                code="PLUGIN_SANDBOX_EXECUTION_FAILED",
                status=500,
                title="Result Panel Execution Error",
                detail=detail,
            )


def fr_plug_sandbox_result_panels(
    request: RenderResultPanelsRequest,
    service: ResultPanelsService | None = None,
    config: ResultPanelsConfig | None = None,
) -> RenderResultPanelsSuccess | PluginFailure:
    """Requirement implementation trace for FR-PLUG-SANDBOX_RESULT_PANELS.

    Args:
        request: RenderResultPanelsRequest instance.
        service: Optional ResultPanelsService instance.
        config: Optional configuration limits.

    Returns:
        RenderResultPanelsSuccess or PluginFailure outcome.
    """
    svc = service or ResultPanelsService(config=config)
    return asyncio.run(svc.render_result_panels(request))


def _run_usage_example() -> None:
    """Execute the bounded public usage demonstration and verification harness.

    Raises:
        RuntimeError: If verification assertion fails.
        TypeError: If response type check fails.
    """
    print("=== Demonstrating FR-PLUG-SANDBOX_RESULT_PANELS Usage ===")
    service = ResultPanelsService()

    panel_1 = ResultPanelDescriptor(
        panel_id="panel.analytics.volatility",
        contribution_id="contrib.analytics.surface",
        plugin_id="com.haruquantai.analytics",
        title="Volatility Surface Panel",
        bridge_operations=("READ_RESULTS", "QUERY_DATA"),
        content_source="app://plugins/com.haruquantai.analytics/panels/volatility.html",
    )
    panel_2 = ResultPanelDescriptor(
        panel_id="panel.analytics.drawdown",
        contribution_id="contrib.analytics.performance",
        plugin_id="com.haruquantai.analytics",
        title="Drawdown Analysis Panel",
        bridge_operations=("READ_RESULTS", "RECEIVE_MESSAGES"),
        content_source="https://cdn.haruquantai.com/plugins/drawdown/index.html",
    )

    service.register_panel(panel_1)
    service.register_panel(panel_2)

    req_id = str(uuid.uuid7())
    snapshot_id = str(uuid.uuid7())

    # 1. Describe all panels
    describe_req = RenderResultPanelsRequest(
        request_id=req_id,
        capability_snapshot_id=snapshot_id,
        operation="DESCRIBE_PANELS",
        contribution_id=None,
    )
    response = asyncio.run(service.render_result_panels(describe_req))
    if not isinstance(response, RenderResultPanelsSuccess):
        err_msg = f"Expected RenderResultPanelsSuccess, got {response}"
        raise TypeError(err_msg)

    print(f"1. Successfully described {len(response.panels)} result panels:")
    for p in response.panels:
        print(f"   - Panel ID: {p.panel_id}, Title: '{p.title}'")

    # 2. Resolve single panel
    resolve_req = RenderResultPanelsRequest(
        request_id=str(uuid.uuid7()),
        capability_snapshot_id=snapshot_id,
        operation="RESOLVE_PANEL",
        panel_id="panel.analytics.volatility",
    )
    resolve_resp = asyncio.run(service.render_result_panels(resolve_req))
    if (
        not isinstance(resolve_resp, RenderResultPanelsSuccess)
        or len(resolve_resp.panels) != 1
    ):
        err_msg = "Expected single panel resolution"
        raise RuntimeError(err_msg)
    print(f"2. Successfully resolved panel '{resolve_resp.panels[0].panel_id}'")

    # 3. Verify trace function
    trace_res = fr_plug_sandbox_result_panels(resolve_req, service=service)
    if not isinstance(trace_res, RenderResultPanelsSuccess):
        err_msg = "fr_plug_sandbox_result_panels failed"
        raise TypeError(err_msg)
    print("3. Trace function fr_plug_sandbox_result_panels verified.")

    # 4. Insecure content source rejection
    bad_panel = ResultPanelDescriptor(
        panel_id="panel.bad.script",
        contribution_id="contrib.bad",
        plugin_id="com.haruquantai.bad",
        title="Malicious Panel",
        bridge_operations=("READ_RESULTS",),
        content_source="javascript:alert(document.cookie)",
    )
    service.register_panel(bad_panel)
    bad_resolve_req = RenderResultPanelsRequest(
        request_id=str(uuid.uuid7()),
        capability_snapshot_id=snapshot_id,
        operation="RESOLVE_PANEL",
        panel_id="panel.bad.script",
    )
    bad_resp = asyncio.run(service.render_result_panels(bad_resolve_req))
    if (
        not isinstance(bad_resp, PluginFailure)
        or bad_resp.code != "PLUGIN_PERMISSION_DENIED"
    ):
        err_msg = "Expected insecure content source failure"
        raise RuntimeError(err_msg)
    print(f"4. Verified insecure content source rejection: {bad_resp.problem.detail}")

    print("=== Usage demonstration completed successfully ===")


if __name__ == "__main__":
    _run_usage_example()
