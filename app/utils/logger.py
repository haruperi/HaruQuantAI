"""Structured logging configuration and logger export for HaruQuantAI.

This module provides the central loguru logger export and setup functions to
configure file logging with rotation, retention, and compression policies.
"""

from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger

__all__ = ["logger", "setup_logging"]


def setup_logging() -> None:
    """Configure loguru to log to stdout and rotating files under data/logs.

    Creates rotating log files for application events, authentication/access
    logs, raw debug statements, and high-severity errors.
    """
    # Ensure logs directory exists
    log_dir = Path("data/logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    # Clear any default handler
    logger.remove()

    # 1. Console handler for standard stdout output
    logger.add(sys.stdout, level="DEBUG")

    # 2. app.log - Rotating file for all logs
    logger.add(
        log_dir / "app.log",
        level="DEBUG",
        rotation="10 MB",
        retention="10 days",
        compression="zip",
        enqueue=True,
    )

    # 3. access.log - Rotating file for auth/access related logs
    # Filter matches logs bound with log_type="access"
    logger.add(
        log_dir / "access.log",
        filter=lambda record: record["extra"].get("log_type") == "access",
        rotation="10 MB",
        retention="10 days",
        compression="zip",
        enqueue=True,
    )

    # 4. debug.log - Rotating file for debug level logs only
    # Filter matches records whose exact level is DEBUG
    logger.add(
        log_dir / "debug.log",
        filter=lambda record: record["level"].name == "DEBUG",
        rotation="10 MB",
        retention="10 days",
        compression="zip",
        enqueue=True,
    )

    # 5. errors.log - Rotating file for error and critical level logs
    logger.add(
        log_dir / "errors.log",
        level="ERROR",
        rotation="10 MB",
        retention="10 days",
        compression="zip",
        enqueue=True,
    )
