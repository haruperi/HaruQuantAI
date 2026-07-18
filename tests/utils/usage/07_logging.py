"""Executable structured logging examples."""

import sys
import tempfile
from pathlib import Path

# Add project root to path before importing local modules
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.utils.logging import (
    configure_logging,
    flush_logging,
    get_logger,
    logger,
    shutdown_logging,
)
from app.utils.settings import load_settings

# Configure logging synchronously to sys.stdout at the start of the script
# for deterministic, inline terminal output ordering.
_initial_settings = load_settings(
    explicit_values={
        "LOG_ENQUEUE": "false",
        "LOG_LEVEL": "DEBUG",
        "LOG_RENDER": "human",
        "LOG_DIRECTORY": "",
    }
)


def _header(title: str) -> None:
    """Print the header for an example section.

    Args:
        title: The title of the section to display.
    """
    sys.stdout.flush()
    print(f"\n\n\n{'=' * 100}")
    print(f"\t\t{title}\t")
    print(f"{'=' * 100}\n")
    sys.stdout.flush()


_header("Example 1: Emit every standard level through the default logger.")
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
logger.critical("Critical message")


configure_logging(_initial_settings.logging)


_header("Example 2: Returns a logger instance for the named module.")
app_logger = get_logger("my_application")
print("App Logger:", app_logger)


_header("Example 3: Emit synthetic secret-like values for redaction verification.")
logger.bind(password="hidden").info("token=abc123")


_header("Example 4: Logger bound with context (correlation_id).")
logger.bind(request_id="req-example").info("context")


_header("Example 5: Capture a traceback through the bound logger.")


def fail() -> None:
    raise ValueError("safe failure")


try:
    fail()
except ValueError:
    logger.exception("captured")


_header("Example 6: Emit access, debug, and error records.")
logger.bind(log_type="access").info("access")
logger.debug("debug route")
logger.error("error route")


_header("Example 7: Sets up structured logging sinks and configuration.")
with tempfile.TemporaryDirectory() as tmp_dir:
    settings = load_settings(
        {
            "LOG_DIRECTORY": tmp_dir,
            "LOG_LEVEL": "DEBUG",
            "LOG_RENDER": "human",
        }
    )
    configure_logging(settings.logging)
    logger.info("Structured logging configured successfully.")

    flush_logging()
    shutdown_logging()


print("Logging lifecycle completed successfully.")
