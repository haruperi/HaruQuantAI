"""Portfolio Composer workspace state and workflow coordinator.

Description:
    Manages workspace session state, coordinates candidate strategy members,
    binds defaults, and aggregates chart and execution log projections.
Purpose:
    FEAT-PORTFOLIO-COMPOSER: Configure composition and evaluation.
Key Capabilities:
    - FR-composer-workspace-state: Query and initialize workspace state.
Python API Usage:
    from app.workspace.portfolio_composer.app_portfolio_composer import (
        AppPortfolioComposerService,
        ComposerWorkspaceState,
    )
    resp = AppPortfolioComposerService().get_workspace_state("proj_1")
CLI Usage:
    uv run python -m pytest tests/workspace/portfolio_composer
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, cast

from app.core.host.logging import get_logger
from app.core.lib.responses import StandardResponse
from app.workspace.portfolio_composer.defaults import (
    ComposerDefaults,
    ComposerViewDefaults,
)
from app.workspace.portfolio_composer.portfolio_composer import (
    ComposerMemberSpec,
    ComposerRunReceipt,
)

logger = get_logger(__name__)


def _to_json_compatible(value: Any) -> Any:
    """Recursively convert tuples and dataclasses to lists and JSON primitives."""
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        return value
    if isinstance(value, (list, tuple)):
        return [_to_json_compatible(item) for item in value]
    if isinstance(value, dict):
        return {str(k): _to_json_compatible(v) for k, v in value.items()}
    if hasattr(value, "__dataclass_fields__"):
        return _to_json_compatible(asdict(value))
    return str(value)


def _build_typed_response[T](
    *,
    request_id: str,
    data: T,
    json_payload: Any,
    revision: int | None = None,
) -> StandardResponse[T]:
    """Validate json_payload through StandardResponse and attach typed data."""
    envelope: StandardResponse[Any] = StandardResponse(
        request_id=request_id,
        data=_to_json_compatible(json_payload),
        revision=revision,
    )
    object.__setattr__(envelope, "data", data)
    return cast("StandardResponse[T]", envelope)


@dataclass(frozen=True, slots=True)
class ComposerWorkspaceState:
    """Consolidated state of the Portfolio Composer workspace."""

    project_id: str
    defaults: ComposerViewDefaults
    members: tuple[ComposerMemberSpec, ...] = field(default_factory=tuple)
    latest_receipt: ComposerRunReceipt | None = None
    is_computing: bool = False


class AppPortfolioComposerService:
    """Top-level workspace coordinator for Portfolio Composer."""

    def __init__(self) -> None:
        self._states: dict[str, ComposerWorkspaceState] = {}

    def get_workspace_state(
        self,
        project_id: str,
        *,
        today_label: str = "2026-01-01",
    ) -> StandardResponse[ComposerWorkspaceState]:
        """Retrieve existing workspace state or initialize a fresh state from defaults.

        Args:
            project_id: Identifier of the active project.
            today_label: Preformatted date label string for view defaults.

        Returns:
            StandardResponse containing ComposerWorkspaceState.
        """
        logger.info(
            "FR-composer-workspace-state: retrieving state for %s today=%s",
            project_id,
            today_label,
        )

        state = self._states.get(project_id)
        if state is None:
            defaults = ComposerDefaults.create(today_label=today_label)
            state = ComposerWorkspaceState(
                project_id=project_id,
                defaults=defaults,
                members=(),
                latest_receipt=None,
                is_computing=False,
            )
            self._states[project_id] = state

        return _build_typed_response(
            request_id=f"ws-{project_id}",
            data=state,
            json_payload=asdict(state),
        )

    def set_workspace_state(
        self,
        project_id: str,
        state: ComposerWorkspaceState,
    ) -> None:
        """Update the stored workspace state for a project."""
        self._states[project_id] = state
