"""Private central resolution point for every bounded DATA limit.

Before ``CAP-DATA-026`` each capability module declared its own limit constants, so a
caller had to know which module owned a bound in order to read it, and a workflow
context could not adjust a bound without editing the owning module. This manifest is
the single place a limit is resolved.

**This module declares values; it does not import them.** ``limits`` sits directly
above ``models`` and ``errors`` in the dependency graph, so importing a constant from
``retrieval`` or ``scheduler`` would invert the layering and reintroduce the cycles the
restructure exists to remove. Equality with the legacy constants is proven instead by
``tests/data/unit/test_limits.py``, which imports both sides and asserts every value
matches. That test is the guard against drift while both definitions coexist; the
legacy constants are deleted in Phase 11.

Workflow overrides never loosen a governed bound. ``research`` may raise a limit
because its output is not execution-bound; ``validation``, ``risk``, and
``execution_bound`` may only tighten one. ``apply_workflow_override`` enforces that
asymmetry rather than trusting callers.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import Final

from app.services.data.contracts import DataError
from app.utils import logger

WORKFLOW_CONTEXTS: Final[tuple[str, ...]] = (
    "research",
    "backtest",
    "validation",
    "risk",
    "execution_bound",
)

_LOOSENING_WORKFLOWS: Final[frozenset[str]] = frozenset({"research"})

DEFAULT_LIMITS: Final[Mapping[str, int]] = MappingProxyType(
    {
        # Retrieval response bounds. OHLCV record count is caller-selected; the
        # chunked backfill workflow owns its own bounded chunk size.
        "TICK_MAX_LIMIT": 250_000,
        "SPREAD_MAX_LIMIT": 250_000,
        "SYMBOL_LIST_DEFAULT_LIMIT": 1_000,
        "SYMBOL_LIST_MAX_LIMIT": 10_000,
        "AVAILABILITY_SCAN_MAX_RECORDS": 1_000_000,
        # Cache identity and expiry bounds.
        "CACHE_TTL_DEFAULT": 3_600,
        "CACHE_TTL_MAX_SECONDS": 604_800,
        "CACHE_TTL_DAILY_SECONDS": 86_400,
        "CACHE_TTL_INTRADAY_SECONDS": 3_600,
        "CACHE_TTL_TICK_SECONDS": 900,
        "CACHE_CLEAR_MAX_ENTRIES": 10_000,
        # Generation bounds.
        "SYNTHETIC_BAR_MAX_RECORDS": 100_000,
        "SYNTHETIC_TICK_MAX_RECORDS": 250_000,
        "MAX_SYNTHETIC_RECORDS": 250_000,
        "GENERATED_TICKS_MIN_PER_BAR": 4,
        # Scheduler and backfill bounds.
        "BACKFILL_CHUNK_SIZE": 10_000,
        "BACKFILL_MAX_RECORDS_PER_CHUNK": 10_000,
        "JOB_MAX_SYMBOLS": 500,
        "JOB_MAX_TIMEFRAMES": 20,
        "JOB_MIN_INTERVAL_SECONDS": 60,
        "JOB_LEASE_TIMEOUT_SECONDS": 300,
        "SCHEDULER_POLL_INTERVAL": 300,
        # Diagnostic payload bounds.
        "QUALITY_SAMPLE_LIMIT": 1_000,
        "AUDIT_QUERY_HARD_MAX_LIMIT": 1_000,
        "ERROR_SAFE_DETAILS_MAX_ITEMS": 64,
        "ERROR_SAFE_DETAILS_MAX_BYTES": 8_192,
    }
)


def get_limit(limit_name: str, workflow: str | None = None) -> int:
    """Resolve one bounded DATA limit, optionally for a declared workflow context.

    Args:
        limit_name: Name of the limit to resolve, as published in ``DEFAULT_LIMITS``.
        workflow: Optional workflow context whose override should be applied. ``None``
            resolves the ungoverned default.

    Returns:
        The resolved positive integer limit.

    Raises:
        DataError: With code ``INVALID_INPUT`` if the limit name is not published or
            the workflow context is not recognized. An unknown limit fails rather than
            returning a permissive default, so a typo cannot silently remove a bound.
    """
    logger.debug("Resolving DATA limit %s for workflow %s", limit_name, workflow)
    if limit_name not in DEFAULT_LIMITS:
        raise DataError(
            "INVALID_INPUT",
            safe_details={"limit": limit_name, "reason": "unknown_limit"},
        )
    if workflow is not None and workflow not in WORKFLOW_CONTEXTS:
        raise DataError(
            "INVALID_INPUT",
            safe_details={"workflow": workflow, "reason": "unknown_workflow"},
        )
    return DEFAULT_LIMITS[limit_name]


def apply_workflow_override(
    workflow: str,
    limits: Mapping[str, int],
) -> Mapping[str, int]:
    """Apply caller-declared limit overrides for one workflow context.

    Args:
        workflow: Workflow context the overrides apply to.
        limits: Mapping of limit name to overriding value.

    Returns:
        An immutable mapping of every published limit with the accepted overrides
        applied.

    Raises:
        DataError: With code ``INVALID_INPUT`` for an unknown workflow, an unknown
            limit name, or a non-positive value. With code ``POLICY_BLOCKED`` when a
            governed workflow attempts to raise a bound; only ``research`` may loosen
            a limit, because its output never reaches an execution-bound decision.
    """
    logger.debug("Applying DATA limit overrides for workflow %s", workflow)
    if workflow not in WORKFLOW_CONTEXTS:
        raise DataError(
            "INVALID_INPUT",
            safe_details={"workflow": workflow, "reason": "unknown_workflow"},
        )

    resolved = dict(DEFAULT_LIMITS)
    for name, value in limits.items():
        if name not in DEFAULT_LIMITS:
            raise DataError(
                "INVALID_INPUT",
                safe_details={"limit": name, "reason": "unknown_limit"},
            )
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise DataError(
                "INVALID_INPUT",
                safe_details={"limit": name, "reason": "non_positive_limit"},
            )
        if value > DEFAULT_LIMITS[name] and workflow not in _LOOSENING_WORKFLOWS:
            raise DataError(
                "POLICY_BLOCKED",
                safe_details={
                    "limit": name,
                    "workflow": workflow,
                    "reason": "governed_workflow_cannot_raise_limit",
                },
            )
        resolved[name] = value

    return MappingProxyType(resolved)


__all__ = [
    "DEFAULT_LIMITS",
    "WORKFLOW_CONTEXTS",
    "apply_workflow_override",
    "get_limit",
]
