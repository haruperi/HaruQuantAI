"""Configuration for Connector Synchronization feature."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from app.contracts.data.models import DeduplicationPolicy


@dataclass(frozen=True)
class ConnectorSyncConfig:
    """Runtime configuration for Connector Synchronization feature.

    Attributes:
        default_overlap_window_seconds: Default overlap seconds.
        default_deduplication_policy: Default policy for deduplication.
        default_revision_policy: Default revision detection strategy.
        max_records_per_page: Maximum records allowed per sync request.
        max_rate_limit_per_window: Default max requests per window.
        rate_limit_window_seconds: Default rate limit window in seconds.
        strict_secret_isolation: Whether secret isolation is enforced.
    """

    default_overlap_window_seconds: int = 300
    default_deduplication_policy: DeduplicationPolicy = "KEEP_FIRST"
    default_revision_policy: Literal["COMPARE_OVERLAP", "FULL_RESCAN"] = (
        "COMPARE_OVERLAP"
    )
    max_records_per_page: int = 50000
    max_rate_limit_per_window: int = 100
    rate_limit_window_seconds: int = 60
    strict_secret_isolation: bool = True

    def __post_init__(self) -> None:
        """Validate configuration parameters.

        Raises:
            ValueError: If parameters violate bounds or literal domains.
        """
        if self.default_overlap_window_seconds < 0:
            msg = "default_overlap_window_seconds must be non-negative"
            raise ValueError(msg)
        if self.max_records_per_page < 1:
            msg = "max_records_per_page must be at least 1"
            raise ValueError(msg)
        if self.max_rate_limit_per_window < 1:
            msg = "max_rate_limit_per_window must be at least 1"
            raise ValueError(msg)
        if self.rate_limit_window_seconds < 1:
            msg = "rate_limit_window_seconds must be at least 1"
            raise ValueError(msg)
        if self.default_deduplication_policy not in (
            "KEEP_FIRST",
            "KEEP_LAST",
            "REJECT",
        ):
            msg = (
                "Invalid default_deduplication_policy:"
                f" {self.default_deduplication_policy}"
            )
            raise ValueError(msg)
        if self.default_revision_policy not in (
            "COMPARE_OVERLAP",
            "FULL_RESCAN",
        ):
            msg = f"Invalid default_revision_policy: {self.default_revision_policy}"
            raise ValueError(msg)
