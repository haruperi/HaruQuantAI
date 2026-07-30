"""Metric sink abstractions and deterministic in-process implementation."""

from __future__ import annotations

import os
import threading
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from typing import Final, Protocol

from app.services.api.observability.errors import ValidationError

_DEFAULT_MAX_SERIES: Final = 5000
_DEFAULT_LABEL_CARDINALITY: Final = 50


type LabelPair = tuple[str, str]
type SeriesKey = tuple[str, tuple[LabelPair, ...]]
type MetricSample = tuple[str, Decimal, tuple[LabelPair, ...]]


def _to_int_env(value: str, *, default: int) -> int:
    """Return one bounded integer configuration value.

    Args:
        value: Raw environment value.
        default: Fallback if no value is set.

    Returns:
        Parsed integer value.

    Raises:
        ValidationError: If the value cannot be parsed as a non-negative integer.
    """
    if not value.strip():
        return default
    try:
        candidate = int(value)
    except ValueError as error:
        raise ValidationError("METRICS_CONFIG_INVALID") from error
    if candidate < 1:
        raise ValidationError("METRICS_CONFIG_INVALID")
    return candidate


def _max_series() -> int:
    """Return the configured maximum number of distinct series."""
    return _to_int_env(
        os.getenv("METRICS_MAX_SERIES", str(_DEFAULT_MAX_SERIES)),
        default=_DEFAULT_MAX_SERIES,
    )


def _max_label_cardinality() -> int:
    """Return the configured per-label cardinality bound."""
    return _to_int_env(
        os.getenv("METRICS_MAX_LABEL_CARDINALITY", str(_DEFAULT_LABEL_CARDINALITY)),
        default=_DEFAULT_LABEL_CARDINALITY,
    )


class MetricSink(Protocol):
    """Protocol for sink adapters receiving metric observations."""

    def validate_labels(self, labels: Mapping[str, str]) -> None:
        """Validate one mapping before accepting an observation."""

    def record(self, name: str, value: Decimal, *, labels: Mapping[str, str]) -> None:
        """Record one metric sample."""

    def snapshot(self) -> tuple[MetricSample, ...]:
        """Return one immutable snapshot of current samples."""


@dataclass(frozen=True, slots=True)
class _InProcessSeries:
    """Immutable metric record returned by the in-process sink."""

    name: str
    labels: tuple[LabelPair, ...]
    value: Decimal

    def __iter__(self) -> tuple[tuple[str, Decimal, tuple[LabelPair, ...]], ...]:
        """Expose one protocol-compatible tuple payload.

        Returns:
            The validated, bounded result.
        """
        return ((self.name, self.value, self.labels),)


class InProcessMetricSink:
    """Deterministic in-process metric sink for tests and local scrape endpoints."""

    def __init__(
        self, *, max_series: int | None = None, max_label_cardinality: int | None = None
    ) -> None:
        """Create one bounded in-process sink.

        Args:
            max_series: Optional override for distinct-series maximum.
            max_label_cardinality: Optional override for per-label cardinality maximum.

        Raises:
            ValidationError: If configured limits are invalid.
        """
        configured_series = max_series if max_series is not None else _max_series()
        configured_cardinality = (
            max_label_cardinality
            if max_label_cardinality is not None
            else _max_label_cardinality()
        )
        if configured_series < 1 or configured_cardinality < 1:
            raise ValidationError("METRICS_CONFIG_INVALID")

        self._lock = threading.RLock()
        self._max_series = configured_series
        self._max_label_cardinality = configured_cardinality
        self._series: dict[SeriesKey, Decimal] = {}
        self._label_values: dict[str, set[str]] = {}

    def validate_labels(self, labels: Mapping[str, str]) -> None:
        """Enforce per-label cardinality bounds before record mutation.

        Raises:
            ValidationError: If the declared validation fails.
        """
        with self._lock:
            for key, value in labels.items():
                allowed = self._label_values.setdefault(key, set())
                if value not in allowed and len(allowed) >= self._max_label_cardinality:
                    raise ValidationError("METRICS_LABEL_CARDINALITY_EXCEEDED")
                allowed.add(value)

    def record(self, name: str, value: Decimal, *, labels: Mapping[str, str]) -> None:
        """Persist one metric sample, preserving latest value per name/label set."""
        key = self._series_key(name, labels)
        with self._lock:
            self._series[key] = value
            self._enforce_series_cap(max_series=self._max_series)

    def snapshot(self) -> tuple[MetricSample, ...]:
        """Return an immutable point-in-time snapshot of all visible samples."""
        with self._lock:
            return tuple(
                (name, value, labels) for (name, labels), value in self._series.items()
            )

    def _series_key(self, name: str, labels: Mapping[str, str]) -> SeriesKey:
        """Build one canonical series key.

        Returns:
            The validated, bounded result.
        """
        normalized = tuple(
            sorted((str(key), str(value)) for key, value in labels.items())
        )
        return (name, normalized)

    def _enforce_series_cap(self, *, max_series: int) -> None:
        """Reject unlimited series growth immediately when limit is exceeded.

        Raises:
            ValidationError: If the declared validation fails.
        """
        if len(self._series) > max_series:
            raise ValidationError("METRICS_MAX_SERIES_EXCEEDED")


__all__ = (
    "InProcessMetricSink",
    "MetricSink",
)
