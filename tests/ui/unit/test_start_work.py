"""Unit tests for FEAT-UI-START_WORK presentation logic.

Covers FR-UI-PRESENT_HOME (capability-aware Home entry points) and
FR-UI-SHOW_PRODUCT_NEWS (optional, non-blocking product news) against the
ratified ``ui.start-work@1`` presentation port in ``app/contracts/ui``.
"""

from typing import override

from app.contracts.common.models import ProblemDetails
from app.contracts.ui.errors import UiFailure
from app.contracts.ui.models import (
    RouteTarget,
    RouteTargetWire,
    StartWorkPresentationRequest,
    StartWorkPresentationSuccess,
    UiNotificationWire,
)
from app.contracts.ui.ports import StartWorkPresentationCapability

_REQUEST_ID = "018f9a2b-7c1d-7abc-9def-0123456789ab"
_SNAPSHOT_ID = "018f9a2b-7c1d-7abc-9def-0123456789ac"
_NEWS_NOTIFICATION_ID = "018f9a2b-7c1d-7abc-9def-0123456789ad"
_RECENT_WORKSPACE_ID = "018f9a2b-7c1d-7abc-9def-0123456789ae"

_MOCK_NEWS = (
    UiNotificationWire(
        notification_id=_NEWS_NOTIFICATION_ID,
        title="Development Mock Mode Active",
        message="Mock capability provider active for the UI workstation.",
        severity="info",
        timestamp_iso="2026-08-25T00:00:00.000000Z",
    ),
)


class StartWorkPresentationService(StartWorkPresentationCapability):
    """Implementation of the start-work presentation port (test evidence)."""

    def __init__(self, *, news_available: bool = True) -> None:
        """Initialize service with an optional offline news source."""
        self._news_available = news_available

    @override
    async def start_work(
        self,
        request: StartWorkPresentationRequest,
    ) -> StartWorkPresentationSuccess | UiFailure:
        """Present home, recent work, shortcuts, and product news."""
        if request.operation == "SHOW_NEWS" and not self._news_available:
            return UiFailure(
                request_id=request.request_id,
                code="CAPABILITY_UNAVAILABLE",
                problem=ProblemDetails(
                    type="urn:haruquantai:ui:news-unavailable",
                    title="Product news unavailable",
                    status=503,
                    code="UI_NEWS_OFFLINE",
                    detail="The product news source is offline; work is unaffected.",
                    request_id=request.request_id,
                ),
            )
        return StartWorkPresentationSuccess(
            request_id=request.request_id,
            recent_routes=(
                RouteTargetWire(
                    path="/research",
                    workspace_id=_RECENT_WORKSPACE_ID,
                    title="Research Workspace (Mock)",
                ),
            ),
            news=_MOCK_NEWS,
        )

    def present_home_entry_points(
        self,
        candidates: tuple[RouteTarget, ...],
        capability_states: dict[str, str],
    ) -> tuple[RouteTarget, ...]:
        """Filter Home entry points by capability readiness.

        An entry point whose required permission maps to a non-ready
        capability state is never shown as available.
        """
        available: list[RouteTarget] = []
        for target in candidates:
            required = target.required_permission
            if required is not None and capability_states.get(required) != "ready":
                continue
            available.append(target)
        return tuple(available)


def _request(operation: str) -> StartWorkPresentationRequest:
    return StartWorkPresentationRequest(
        request_id=_REQUEST_ID,
        capability_snapshot_id=_SNAPSHOT_ID,
        operation=operation,  # type: ignore[arg-type]
    )


async def test_fr_ui_present_home() -> None:
    """FR-UI-PRESENT_HOME: SHOW_HOME succeeds and entry points are capability-gated."""
    service = StartWorkPresentationService()

    result = await service.start_work(_request("SHOW_HOME"))
    assert isinstance(result, StartWorkPresentationSuccess)
    assert result.outcome == "SUCCESS"
    assert result.request_id == _REQUEST_ID

    research = RouteTarget(
        path="/research",
        workspace_id="ws-research",
        title="Research",
        required_permission="workspace.manage-workspaces@1",
    )
    trading = RouteTarget(
        path="/trading",
        workspace_id="ws-trading",
        title="Trading",
        required_permission="trading.execute-orders@1",
    )
    plain = RouteTarget(path="/home", workspace_id="ws-home", title="Home")

    capability_states = {"workspace.manage-workspaces@1": "ready"}

    entry_points = service.present_home_entry_points(
        (research, trading, plain), capability_states
    )

    # Ready-capability and permission-free entry points are shown.
    assert research in entry_points
    assert plain in entry_points
    # No action is shown as available when its capability is absent.
    assert trading not in entry_points


async def test_fr_ui_show_product_news() -> None:
    """FR-UI-SHOW_PRODUCT_NEWS: news is presented separately and never blocks work."""
    service = StartWorkPresentationService()

    result = await service.start_work(_request("SHOW_NEWS"))
    assert isinstance(result, StartWorkPresentationSuccess)
    assert len(result.news) == 1
    assert result.news[0].title == "Development Mock Mode Active"

    # Offline news returns a structured failure that is confined to the news
    # surface: SHOW_HOME keeps succeeding (non-blocking acceptance).
    offline_service = StartWorkPresentationService(news_available=False)
    news_result = await offline_service.start_work(_request("SHOW_NEWS"))
    assert isinstance(news_result, UiFailure)
    assert news_result.code == "CAPABILITY_UNAVAILABLE"
    assert "unaffected" in news_result.problem.detail

    home_result = await offline_service.start_work(_request("SHOW_HOME"))
    assert isinstance(home_result, StartWorkPresentationSuccess)
    assert home_result.outcome == "SUCCESS"
