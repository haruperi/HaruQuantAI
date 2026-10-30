"""Databank result persistence contracts and store service."""

from __future__ import annotations

from app.core.trading.results.contracts import ResultSummary, RunResult
from app.core.trading.results.store import ResultStore

__all__ = [
    "ResultStore",
    "ResultSummary",
    "RunResult",
]
