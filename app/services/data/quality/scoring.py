"""Private helpers shared by the quality detectors.

``_issue`` and ``_samples`` are needed by both ``ohlcv_validator`` and ``adversarial``.
Hosting them in either one would make the two import each other, so they live here —
below both — instead. Nothing outside ``quality`` imports this module.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from app.services.data.contracts.dataset import QualityIssue

if TYPE_CHECKING:
    from collections.abc import Sequence

_MAX_SAMPLES: Final = 10
_MIN_SPIKE_RECORDS: Final = 3
_MIN_GAP_RECORDS: Final = 2


def _samples(values: Sequence[str], limit: int) -> tuple[tuple[str, ...], bool]:
    """Return bounded samples and whether they were truncated."""
    bounded = tuple(values[:limit])
    return bounded, len(values) > limit


def _issue(
    code: str,
    severity: str,
    message: str,
    affected: int,
    samples: Sequence[str],
    limit: int,
) -> QualityIssue:
    """Build one bounded diagnostic honouring the sample limit."""
    bounded, _ = _samples(samples, limit)
    return QualityIssue(
        code=code,
        severity=severity,  # type: ignore[arg-type]
        message=message,
        affected_count=affected,
        samples=bounded,
    )


def _fit_samples(
    issues: Sequence[QualityIssue], limit: int
) -> tuple[tuple[QualityIssue, ...], bool]:
    """Distribute the shared sample budget across detected issues.

    The report contract bounds the *total* number of samples, so each issue
    receives an equal share and any surplus evidence is disclosed as truncated.

    Returns:
        The issues with fitted samples, and whether any evidence was dropped.
    """
    if not issues:
        return (), False
    share = max(1, limit // len(issues))
    fitted: list[QualityIssue] = []
    truncated = False
    for issue in issues:
        if len(issue.samples) > share:
            truncated = True
        kept = issue.samples[:share]
        if (issue.affected_count or 0) > len(kept):
            truncated = True
        fitted.append(issue.model_copy(update={"samples": kept}))
    return tuple(fitted), truncated
