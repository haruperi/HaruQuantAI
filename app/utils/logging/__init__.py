"""Expose import-safe structured logging and its explicit lifecycle.

Handler installation remains lazy or explicitly requested; importing this
feature package does not configure logging or touch the filesystem.
"""

from app.utils.logging.logger import (
    BoundLogger,
    RedactingFilter,
    StructuredFormatter,
    configure_logging,
    flush_logging,
    get_logger,
    logger,
    shutdown_logging,
)

__all__ = (
    "BoundLogger",
    "RedactingFilter",
    "StructuredFormatter",
    "configure_logging",
    "flush_logging",
    "get_logger",
    "logger",
    "shutdown_logging",
)
