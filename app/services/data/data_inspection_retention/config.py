"""Configuration for Data Inspection, Export, and Retention feature."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DataInspectionRetentionConfig:
    """Runtime configuration for Data Inspection, Export, and Retention.

    Attributes:
        default_preview_limit: Default maximum rows returned in a preview.
        max_preview_limit: Upper bound limit on preview rows to keep memory
            within budget.
        default_quarantine_days: Default quarantine period in days before
            unreachable artifacts can be collected.
        supported_export_formats: Tuple of supported export format strings.
    """

    default_preview_limit: int = 100
    max_preview_limit: int = 10_000
    default_quarantine_days: int = 30
    supported_export_formats: tuple[str, ...] = ("CSV", "PARQUET")

    def __post_init__(self) -> None:
        """Validate configuration settings.

        Raises:
            ValueError: If settings are out of valid bounds.
        """
        if self.default_preview_limit <= 0:
            msg = "default_preview_limit must be a positive integer"
            raise ValueError(msg)
        if self.max_preview_limit < self.default_preview_limit:
            msg = (
                "max_preview_limit must be greater than or equal to "
                "default_preview_limit"
            )
            raise ValueError(msg)
        if self.default_quarantine_days <= 0:
            msg = "default_quarantine_days must be a positive integer"
            raise ValueError(msg)
        if not self.supported_export_formats:
            msg = "supported_export_formats cannot be empty"
            raise ValueError(msg)
