"""Demonstrate structured logger levels, context, exceptions, and routing."""

import logging
import os
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

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


def example_logger_access() -> None:
    """Verify named logger access does not configure a second handler tree."""
    assert get_logger("usage").name == "haruquant.usage"


def example_logger_redaction(log_directory: Path) -> None:
    """Emit sensitive text for post-shutdown redaction verification."""
    logger.info("token=usage-secret")
    flush_logging()


def example_sink_failure(log_directory: Path) -> None:
    """Verify an invalid real sink fails closed."""
    try:
        configure_logging(
            LoggingSettings(
                file_path=log_directory / "missing" / "app.log",
                log_directory=None,
            )
        )
    except ConfigurationError:
        return
    raise AssertionError("invalid logging sink was accepted")


def example_import_safety() -> None:
    """Verify a fresh Utils import installs no logging handlers."""
    project_root = str(Path(__file__).resolve().parents[3])
    command = (
        f"import sys; sys.path.insert(0, {project_root!r}); "
        "import logging, app.utils; "
        "print(len(logging.getLogger('haruquant').handlers))"
    )
    completed = subprocess.run(  # noqa: S603 - fixed interpreter and source.
        [sys.executable, "-c", command],
        check=True,
        capture_output=True,
        text=True,
    )
    assert completed.stdout.strip() == "0"


def example_standard_levels() -> None:
    """Demonstrate standard structured logging levels."""
    print("\n\n 1.1 Standard structured logging levels")
    logger.debug("This is a debug message containing developer details.")
    logger.info("This is an info message for standard application events.")
    logger.warning("This is a warning indicating a potential issue.")
    logger.error("This is an error indicating an execution failure.")
    logger.critical("This is a critical failure message.")
    flush_logging()


def example_exception_logging() -> None:
    """Demonstrate logging exceptions with tracebacks."""
    print("\n\n 1.2 Logging exceptions with tracebacks")
    try:
        _ = 1 / 0
    except ZeroDivisionError:
        logger.exception("Successfully captured an exception with traceback:")
    flush_logging()


def example_bound_context() -> None:
    """Demonstrate dynamic contextual metadata using bind."""
    print("\n\n 1.3 Dynamic context logging using bind (Dynamic Contextual Metadata)")
    bound_logger = logger.bind(request_id="REQ-1002", user_id="USER-A")
    bound_logger.info("Processing order request with contextual metadata.")
    flush_logging()


def example_specialized_routing(log_directory: Path) -> None:
    """Emit records for post-shutdown specialized-route verification."""
    print("\n\n 1.4 Routing to Specialized Log Files")
    access_logger = logger.bind(log_type="access", user_id="USER-A")
    access_logger.info("User logged in successfully from 192.168.1.50")
    debug_logger = logger.bind(log_type="debug", component="usage-example")
    debug_logger.debug("Developer diagnostic routed to debug.log")
    logger.error("Recoverable failure routed to errors.log")
    logger.critical("Critical failure routed to errors.log")
    flush_logging()


def verify_log_files(log_directory: Path) -> None:
    """Verify queued records reached every real default file sink."""
    app_content = (log_directory / "app.log").read_text(encoding="utf-8")
    access_content = (log_directory / "access.log").read_text(encoding="utf-8")
    debug_content = (log_directory / "debug.log").read_text(encoding="utf-8")
    error_content = (log_directory / "errors.log").read_text(encoding="utf-8")

    assert "usage-secret" not in app_content
    assert "[REDACTED]" in app_content
    assert "User logged in successfully" in access_content
    assert "Developer diagnostic routed" in debug_content
    assert "Recoverable failure" in error_content
    assert "Critical failure" in error_content
    print("Verified app.log, access.log, debug.log, and errors.log routing.")


def main() -> None:
    """Configure real sinks, execute every example, and verify routed files."""
    with TemporaryDirectory(prefix="haruquant-usage-") as directory:
        original_directory = Path.cwd()
        os.chdir(directory)
        try:
            settings = LoggingSettings()
            assert settings.log_directory == Path("data/logs")
            assert settings.level == "DEBUG"
            configure_logging()
            configure_logging()
            log_directory = Path("data/logs")
            assert logging.getLogger("haruquant").level == logging.DEBUG
            example_logger_access()
            example_import_safety()
            example_standard_levels()
            example_exception_logging()
            example_bound_context()
            example_logger_redaction(log_directory)
            example_specialized_routing(log_directory)
            example_sink_failure(log_directory)
            shutdown_logging()
            verify_log_files(log_directory)
        finally:
            shutdown_logging()
            os.chdir(original_directory)


if __name__ == "__main__":
    main()
