"""
Utility logging tools and logger API exposed for HaruQuantAI.

Official AI Tools:
    - init_worker_logger
    - configure_multiprocess_listener

The module also exposes the project logger utility so production files can use:

    from tools.utils import logger
"""

# logger.py official AI tools
# logger.py public logging API
from tools.utils.logger import (
    CRITICAL,
    DEBUG,
    DEFAULT_LEVELS,
    ERROR,
    INFO,
    SUCCESS,
    TRACE,
    WARNING,
    CompatRecord,
    Logger,
    StructlogAdapter,
    configure_default_file_sinks,
    configure_multiprocess_listener,
    init_worker_logger,
    logger,
)

__all__ = [
    # logger.py public logging API
    "DEBUG",
    "ERROR",
    "INFO",
    "SUCCESS",
    "TRACE",
    "WARNING",
    "CRITICAL",
    "DEFAULT_LEVELS",
    "CompatRecord",
    "Logger",
    "StructlogAdapter",
    "configure_default_file_sinks",
    "logger",
    # logger.py official AI tools
    "configure_multiprocess_listener",
    "init_worker_logger",
]
