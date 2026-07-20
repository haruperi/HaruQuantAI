"""Operator workflow page-context builder."""

from __future__ import annotations

from app.services.conversation.context.base import build_compact_context
from app.services.schemas.chat import PageContext


def build_operator_workflow_context(**kwargs: object) -> PageContext:
    return build_compact_context(
        **kwargs,  # type: ignore[arg-type]
        page_type="operator_workflow",
        summary_bullets=[
            "Operator workflow context for active tasks, evidence, approvals, incidents, and handoffs."
        ],
    )
