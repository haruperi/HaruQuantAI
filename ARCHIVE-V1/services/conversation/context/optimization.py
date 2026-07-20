"""Optimization page-context builder."""

from __future__ import annotations

from app.services.conversation.context.base import build_compact_context
from app.services.schemas.chat import PageContext


def build_optimization_context(**kwargs: object) -> PageContext:
    return build_compact_context(
        **kwargs,  # type: ignore[arg-type]
        page_type="optimization_detail",
        summary_bullets=[
            "Optimization context for parameter search, candidate ranking, robustness, and overfit checks."
        ],
    )
