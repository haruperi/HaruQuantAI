"""Authenticated initial Edge Lab HTTP boundary."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.services.api.contracts import (
    ResearchRunRequest,  # noqa: TC001 - FastAPI runtime request model
)
from app.services.api.identity import require_auth_context, require_human_permission
from app.services.research import ResearchReport, run_edge_lab_profile
from app.utils import AuthContext, logger

router = APIRouter(prefix="/api/research", tags=["research"])


@router.post("/run", response_model=ResearchReport)
def _run_research(
    request: ResearchRunRequest,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
) -> ResearchReport:
    """Delegate one authenticated bounded run to Research.

    Args:
        request: Validated API-owned Research request.
        auth: Authenticated human principal.

    Returns:
        Registered advisory Research report.
    """
    logger.info("Delegating authenticated Research run")
    require_human_permission(auth, "research:run")
    return run_edge_lab_profile(
        request.dataset,
        hypothesis=request.hypothesis,
        config=request.config,
    )


__all__ = ("router",)
