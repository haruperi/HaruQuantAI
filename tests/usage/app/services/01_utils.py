"""Usage example showing loguru logging in HaruQuantAI."""

import sys
from pathlib import Path

# Add project root to sys.path to allow direct execution
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

import app  # noqa: F401
from loguru import logger


def example_01_loguru_example() -> None:
    """Demonstrate how to log messages at various levels using loguru."""
    logger.info("Initializing loguru usage example.")

    # 1. Standard structured logging levels
    logger.debug("This is a debug message containing developer details.")
    logger.info("This is an info message for standard application events.")
    logger.warning("This is a warning indicating a potential issue.")
    logger.error("This is an error indicating an execution failure.")
    logger.critical("This is a critical failure message.")

    # 2. Logging exceptions with tracebacks
    try:
        _ = 1 / 0
    except ZeroDivisionError:
        logger.exception("Successfully captured an exception with traceback:")

    # 3. Dynamic context logging using bind
    bound_logger = logger.bind(request_id="REQ-1002", user_id="USER-A")
    bound_logger.info("Processing order request with contextual metadata.")

    # 4. Access/Auth specific logging (goes to access.log)
    access_logger = logger.bind(log_type="access", user_id="USER-A")
    access_logger.info("User logged in successfully from 192.168.1.50")

    # Assert that example completed cleanly
    assert True


if __name__ == "__main__":
    example_01_loguru_example()
