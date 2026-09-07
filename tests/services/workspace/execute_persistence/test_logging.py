"""Structured logging and ARCH-003 compliance tests for execute_persistence."""

from __future__ import annotations

import logging

from app.composition.logging import BoundLogger
from app.services.workspace.execute_persistence.execute_persistence import (
    ExecutePersistenceService,
    logger,
)


def test_custom_logger_instance() -> None:
    """Execute persistence logger must be a BoundLogger adhering to ARCH-003."""
    assert isinstance(logger, BoundLogger)


def test_no_root_logger_handlers_added() -> None:
    """Importing or instantiating service must not modify root logging configuration."""
    root_handlers_before = list(logging.root.handlers)
    service = ExecutePersistenceService()
    assert list(logging.root.handlers) == root_handlers_before
    service.close()
