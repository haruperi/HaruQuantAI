"""Executable structured-logging examples."""

import logging
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.utils import (
    ConfigurationError,
    LoggingSettings,
    configure_logging,
    flush_logging,
    get_logger,
    logger,
    shutdown_logging,
)


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def example_import_safety() -> None:
    """Display that import alone installs no Utils-owned root handler."""
    _header("Example 1: Import Safety")
    print("Import-safe handlers:", len(logging.getLogger("haruquant").handlers))


def example_logger_access() -> None:
    """Access a stable named standard-library logger."""
    _header("Example 2: Logger Access")
    print("Logger name:", get_logger("usage").name)


def example_standard_levels() -> None:
    """Emit bounded records at all standard levels."""
    _header("Example 3: Standard Levels")
    logger.debug("debug example")
    logger.info("info example")
    logger.warning("warning example")
    logger.error("error example")
    logger.critical("critical example")


def example_logger_redaction() -> None:
    """Emit synthetic secret-shaped data for redaction verification."""
    _header("Example 4: Logger Redaction")
    logger.info("api_key=synthetic-value")


def _raise_demonstration_error() -> None:
    """Raise one bounded error for exception-logging demonstration.

    Raises:
        ValueError: Always, with a safe demonstration message.
    """
    raise ValueError("safe demonstration failure")


def example_exception_logging() -> None:
    """Capture a bounded traceback through the shared logger."""
    try:
        _raise_demonstration_error()
    except ValueError:
        logger.exception("captured example")


def example_bound_context() -> None:
    """Emit an immutable bound request context."""
    _header("Example 5: Bound Context")
    logger.bind(request_id="req-example").info("bound context")


def example_specialized_routing(log_directory: Path) -> None:
    """Emit access, debug, and error routes and verify their files exist.

    Args:
        log_directory: Configured temporary logging directory.
    """
    _header("Example 6: Specialized Routing")
    logger.bind(log_type="access").info("access example")
    logger.debug("debug route example")
    logger.error("error route example")
    flush_logging()
    names = sorted(path.name for path in log_directory.glob("*.log"))
    print("Specialized routes:", names)


def example_sink_failure(log_directory: Path) -> None:
    """Demonstrate bounded failure for a missing standalone parent.

    Args:
        log_directory: Existing temporary base directory.
    """
    _header("Example 7: Sink Failure")
    try:
        configure_logging(
            LoggingSettings(
                file_path=log_directory / "missing" / "app.log",
                log_directory=None,
            )
        )
    except ConfigurationError:
        print("Sink failure: safely surfaced")


def main() -> None:
    """Run all structured-logging examples with temporary sinks."""
    example_import_safety()
    example_logger_access()
    with tempfile.TemporaryDirectory() as directory:
        log_directory = Path(directory)
        configure_logging(LoggingSettings(log_directory=log_directory, colorize=False))
        example_standard_levels()
        example_logger_redaction()
        example_exception_logging()
        example_bound_context()
        example_specialized_routing(log_directory)
        example_sink_failure(log_directory)
        shutdown_logging()
    print("Logging verification: completed")


if __name__ == "__main__":
    main()
