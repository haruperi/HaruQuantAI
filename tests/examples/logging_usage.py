"""Interactive logging walkthrough.

Run `uv run --locked python -m tests.examples.logging_usage` from the project root.
Example log files remain in an isolated temporary folder for you to inspect.
"""

import sys
from pathlib import Path
from tempfile import mkdtemp

from app.kernel.logging import (
    LoggingConfig,
    configure_logging,
    get_logger,
)

logger = get_logger("app.example")


def example_logging() -> None:
    """Demonstrate default logging settings followed by custom configuration."""
    print(
        "\n\n 1.1 Standard structured logging levels (Default Configuration)",
        flush=True,
    )
    # Default settings: level=INFO (20), log_directory="data/logs" (*.jsonl),
    # and console=True. DEBUG is filtered out because default level is INFO.
    with configure_logging(stream=sys.stdout) as default_diagnostics:
        logger.debug("This debug message is filtered out under default INFO level.")
        logger.info("This is an info message using default logging configuration.")
        logger.warning("This is a warning indicating a potential issue.")
        logger.error("This is an error indicating an execution failure.")
        logger.critical("This is a critical failure message.")
        default_diagnostics.flush()

    print(
        "\n\n--- Advanced examples with custom configuration "
        "(DEBUG enabled, isolated temp folder) ---",
        flush=True,
    )
    directory = Path(mkdtemp(prefix="logging-example-"))
    config = LoggingConfig(
        level=10,  # Enable DEBUG so every standard level is visible.
        log_directory=directory,
        colorize=True,
        purposes=("application", "errors", "audit", "access", "debug"),
        secrets=("custom-secret-token-999",),
    )

    # Configure custom scope with isolated log directory and custom routes.
    # Share stdout with the headings and flush between sections for readable order.
    with configure_logging(config, stream=sys.stdout) as diagnostics:
        print("\n\n 1.2 Logging exceptions with tracebacks", flush=True)
        # Inside an except block, exception() captures the exception type and
        # traceback function/line locations, omitting sensitive messages and locals.
        try:
            _ = 1 / 0
        except ZeroDivisionError:
            logger.exception("Successfully captured an exception with traceback:")
        diagnostics.flush()

        print(
            "\n\n 1.3 Dynamic context logging using bind (Dynamic Contextual Metadata)",
            flush=True,
        )
        # These fictional identifiers appear under context.request_id and
        # context.user_id in JSON records; the original logger stays unchanged.
        bound_logger = logger.bind(request_id="REQ-1002", user_id="USER-A")
        bound_logger.info("Processing order request with contextual metadata.")
        diagnostics.flush()

        print("\n\n 1.4 Routing to Specialized Log Files", flush=True)
        # purpose selects a declared route. Access/auth events go to access.jsonl.
        access_logger = logger.bind(purpose="access", user_id="USER-A")
        access_logger.info("User logged in successfully from 192.168.1.50")

        # Developer diagnostics go to debug.jsonl when explicitly routed there.
        debug_logger = logger.bind(purpose="debug", component="request_parser")
        debug_logger.debug("Request parsed successfully.", field_count=4)
        diagnostics.flush()

        print("\n\n 1.5 Redacting secret text and sensitive fields", flush=True)
        # Automatic pattern masking redacts recognized credentials (e.g. Bearer tokens).
        # Configured secrets (LoggingConfig.secrets) redact registered opaque tokens.
        # Sensitive context keys (e.g. api_key, password, token) redact their values.
        logger.info(
            "Authenticating via Bearer token-xyz with custom-secret-token-999",
            api_key="super-secret-value",
        )
        diagnostics.flush()

    print(f"\nExample logs are ready to inspect in: {directory}")
    print("  application.jsonl : standard events and contextual metadata")
    print("  errors.jsonl      : errors, critical events, and exceptions")
    print("  access.jsonl      : access/authentication events")
    print("  debug.jsonl       : explicitly routed developer diagnostics")


if __name__ == "__main__":
    example_logging()
