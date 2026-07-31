"""Executable structured-logging examples."""

import logging
import sys
import tempfile
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.utils import (
    configure_logging,
    flush_logging,
    get_logger,
    get_logger_name,
    load_settings,
    log_info,
    shutdown_logging,
)

logger = get_logger(__name__)


def _feature_header(title: str) -> None:
    """Print feature title and module flow banner."""
    print(f"\n\n{'=' * 88}\n{title}\n{'=' * 88}")


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'-' * 88}\n{title}\n{'-' * 88}")


def _format_result(obj: Any) -> str:
    """Dynamically format the output result type and field/key signature."""
    cls = type(obj)
    type_name = cls.__name__
    if hasattr(cls, "model_fields"):
        keys = ", ".join(cls.model_fields.keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    if isinstance(obj, dict):
        keys = ", ".join(obj.keys())
        return f"Output Result -> dict({keys}) : dict"
    if hasattr(obj, "__dict__"):
        keys = ", ".join(vars(obj).keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    return f"Output Result -> {type_name} : {type_name}"


def fr_utils_032_import_safety() -> None:
    """FR-UTL-032: Stage 1 — Display that import alone installs no Utils-owned root handler."""
    _header("Stage 1: Import Safety - Unconfigured Initial State (FR-UTL-032)")
    handlers_count = len(logging.getLogger("haruquant").handlers)
    print(_format_result(handlers_count))
    print(f"Data -> root_handler_count={handlers_count}")


def fr_utils_026_logger_access() -> None:
    """FR-UTL-026: Stage 1 — Access a stable named standard-library logger."""
    _header("Stage 1: Logger Access - Stable Named Logger (FR-UTL-026)")
    log_obj = get_logger("usage")
    log_name = get_logger_name(log_obj)
    print(_format_result(log_obj))
    print(f"Data -> logger_name='{log_name}'")


def fr_utils_027_standard_levels() -> None:
    """FR-UTL-027: Stage 1 — Emit bounded records at all standard levels."""
    _header("Stage 1: Bound Logger Call - Standard Log Levels (FR-UTL-027)")
    logger.debug("debug example")
    logger.info("info example")
    logger.warning("warning example")
    logger.error("error example")
    logger.critical("critical example")
    print(_format_result(logger))
    print("Data -> Emitted log records at DEBUG, INFO, WARNING, ERROR, CRITICAL")


def fr_utils_028_logger_redaction() -> None:
    """FR-UTL-028: Stage 2 — Emit synthetic secret-shaped data for redaction verification."""
    _header("Stage 2: Redact & Format - Logger Secret Redaction (FR-UTL-028)")
    logger.info("api_key=synthetic-value")
    print(_format_result(logger))
    print("Data -> Secret-shaped input redacted before formatting")


def fr_utils_039_bound_context() -> None:
    """FR-UTL-039: Stage 2 — Emit an immutable bound request context."""
    _header("Stage 2: Bound Context - Context Injection (FR-UTL-039)")
    log_info(logger, "bound context example", context={"request_id": "req-example"})
    print(_format_result(logger))
    print("Data -> Structured record enriched with bound request_id='req-example'")


def _raise_demonstration_error() -> None:
    """Raise one bounded error for exception-logging demonstration.

    Raises:
        ValueError: Always, with a safe demonstration message.
    """
    raise ValueError("safe demonstration failure")


def fr_utils_039_exception_logging() -> None:
    """FR-UTL-039: Stage 2 — Capture a bounded traceback through shared logger."""
    _header("Stage 2: Exception Capture - Traceback Logging (FR-UTL-039)")
    try:
        _raise_demonstration_error()
    except ValueError:
        logger.exception("captured demonstration error")
    print(_format_result(logger))
    print(
        "Data -> Captured exception traceback cleanly without leaking unhandled crash"
    )


def fr_utils_040_specialized_routing(log_directory: Path) -> None:
    """FR-UTL-040: Stage 3 — Emit access, debug, and error routes and verify files exist.

    Args:
        log_directory: Configured temporary logging directory.
    """
    _header("Stage 3: Configured Sink Routing - Specialized Routing (FR-UTL-040)")
    log_info(logger, "access example", context={"log_type": "access"})
    logger.debug("debug route example")
    logger.error("error route example")
    flush_logging()
    names = sorted(
        path.name for path in log_directory.glob("*.log") if path.stat().st_size
    )
    assert {"access.log", "debug.log", "errors.log"} <= set(names)
    print(_format_result(names))
    print(f"Data -> non_empty_log_files={names}")


def fr_utils_041_sink_failure(log_directory: Path) -> None:
    """FR-UTL-041: Stage 3 — Demonstrate bounded failure handling for an unwriteable configuration.

    Args:
        log_directory: Existing temporary base directory.
    """
    _header("Stage 3: Configured Sink Failure - Fallback Handling (FR-UTL-041)")
    try:
        configure_logging(
            load_settings().logging.model_copy(
                update={
                    "log_directory": log_directory / "non_existent",
                    "level": "DEBUG",
                }
            )
        )
    except Exception as exc:  # noqa: BLE001 - public logger intentionally hides error classes.
        print(_format_result(exc))
        print(f"Data -> Sink failure safely surfaced ({exc})")


def main() -> None:
    """Run all structured-logging examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-UTIL-07 — logging/ — Structured Logging\n\n"
        "Purpose: Provide import-safe logger access, lazy approved defaults, and explicit redacted structured-handler overrides.\n\n"
        "Module flow:\n"
        "-> runtime bound-logger call\n"
        "-> lazy default or explicit override\n"
        "-> redact\n"
        "-> structured record\n"
        "-> configured sink"
    )

    # Stage 1: Import safety, logger access, and standard bound-logger calls
    fr_utils_032_import_safety()
    fr_utils_026_logger_access()

    with tempfile.TemporaryDirectory() as directory:
        log_directory = Path(directory)
        configure_logging(
            load_settings().logging.model_copy(
                update={"log_directory": log_directory, "level": "DEBUG"}
            )
        )
        # Stage 1 & 2: Bound logger calls, redaction, and bound context
        fr_utils_027_standard_levels()
        fr_utils_028_logger_redaction()
        fr_utils_039_bound_context()
        fr_utils_039_exception_logging()

        # Stage 3: Structured record emission to specialized sinks and failure handling
        fr_utils_040_specialized_routing(log_directory)
        fr_utils_041_sink_failure(log_directory)
        shutdown_logging()


if __name__ == "__main__":
    main()
