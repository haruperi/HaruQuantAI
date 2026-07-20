"""Dashboard page-context builder."""

from __future__ import annotations

from app.services.conversation.context.base import build_compact_context
from app.services.schemas.chat import PageContext


def build_dashboard_context(**kwargs: object) -> PageContext:
    return build_compact_context(
        **kwargs,  # type: ignore[arg-type]
        page_type="dashboard",
        summary_bullets=[
            "Dashboard overview context for portfolio, alerts, KPIs, and current workspace state."
        ],
    )
