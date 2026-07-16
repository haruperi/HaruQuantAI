"""Executable stage-one structured-logging examples."""

import logging
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from app.utils import (
    ConfigurationError,
    LoggingSettings,
    configure_logging,
    flush_logging,
    get_logger,
    logger,
    shutdown_logging,
)


def example_logger_access() -> logging.Logger:
    """Get a stable child logger without configuring handlers."""
    return get_logger("usage")


def example_standard_levels() -> None:
    """Emit every standard level through the bound logger."""
    logger.debug("debug")
    logger.info("info")
    logger.warning("warning")
    logger.error("error")
    logger.critical("critical")


def example_logger_redaction() -> None:
    """Emit synthetic secret-like values for redaction verification."""
    logger.bind(password="hidden").info("token=abc123")


def example_bound_context() -> None:
    """Bind immutable trace context."""
    logger.bind(request_id="req-example").info("context")


def example_exception_logging() -> None:
    """Capture a traceback through the bound logger."""

    def fail() -> None:
        raise ValueError("safe failure")

    try:
        fail()
    except ValueError:
        logger.exception("captured")


def example_specialized_routing() -> None:
    """Emit access, debug, and error records."""
    logger.bind(log_type="access").info("access")
    logger.debug("debug route")
    logger.error("error route")


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
    """Verify a fresh Utils import installs no handlers."""
    command = (
        "import logging; import app.utils; "
        "print(len(logging.getLogger('haruquant').handlers))"
    )
    project_root = str(Path(__file__).resolve().parents[3])
    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH", "")
    if existing_pythonpath:
        env["PYTHONPATH"] = f"{project_root}{os.pathsep}{existing_pythonpath}"
    else:
        env["PYTHONPATH"] = project_root

    completed = subprocess.run(  # noqa: S603
        [sys.executable, "-c", command],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    assert completed.stdout.strip() == "0"


def main() -> None:
    """Run all logging examples in an isolated directory."""
    original = Path.cwd()
    with tempfile.TemporaryDirectory() as temporary:
        directory = Path(temporary)
        try:
            os.chdir(directory)
            assert example_logger_access().handlers == []
            example_standard_levels()
            example_logger_redaction()
            example_bound_context()
            example_exception_logging()
            example_specialized_routing()
            flush_logging()
            shutdown_logging()
            app_log = directory / "data" / "logs" / "app.log"
            records = app_log.read_text(encoding="utf-8")
            assert "abc123" not in records
            assert "hidden" not in records
            example_sink_failure(directory)
            example_import_safety()
            print(
                "Logging verification:",
                {
                    "standard_levels": "emitted",
                    "bound_context": "emitted",
                    "redaction": "verified",
                    "specialized_routes": "verified",
                    "sink_failure": "rejected",
                    "import_handlers": 0,
                },
            )
        finally:
            shutdown_logging()
            os.chdir(original)


if __name__ == "__main__":
    main()
