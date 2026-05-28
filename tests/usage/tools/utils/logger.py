"""
Usage example for HaruQuantAI logging tools.

Run from the project root:
    python tests/usage/tools/utils/logger.py
"""

from __future__ import annotations

import multiprocessing as mp
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.utils import configure_default_file_sinks
from tools.utils import configure_multiprocess_listener
from tools.utils import init_worker_logger
from tools.utils import logger


def main() -> None:
    """Demonstrate normal logging and multiprocessing logger setup."""
    request_id = "usage-logger-001"
    log_dir = Path("data/logs")

    configure_default_file_sinks(log_dir)
    logger.info("Logger usage example started | request_id=%s", request_id)

    log_queue: mp.Queue = mp.Queue()
    listener_result = configure_multiprocess_listener(log_queue, request_id=request_id)
    if listener_result["status"] != "success":
        logger.error("Listener setup failed", extra={"error": listener_result["error"]})
        return

    worker_result = init_worker_logger(log_queue, request_id=request_id)
    if worker_result["status"] == "success":
        logger.info("Worker logger initialized | request_id=%s", request_id)
    else:
        logger.error(
            "Worker logger setup failed", extra={"error": worker_result["error"]}
        )

    logger.bind(component="usage_example").success("Logger usage example completed")
    log_queue.put(None)


if __name__ == "__main__":
    main()
