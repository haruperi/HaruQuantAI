"""Host hardware observations and compute-pool construction.

The bootstrap coordinator calls diagnostics during B09 and owns the pool
returned during I04. Importing this module performs no hardware probe and
starts no workers. A pool provides execution capacity, not research engines.
"""

import os
import platform
from concurrent.futures import ProcessPoolExecutor
from typing import Any

import psutil

from app.host.logging import get_logger

logger = get_logger(__name__)


def diagnostics() -> dict[str, Any]:
    """Collect a point-in-time CPU, memory, OS, and Python snapshot.

    Queries psutil and platform synchronously, then logs collection without host
    identifiers. Hardware-query failures propagate; results are not a resource
    reservation.

    Returns:
        Mapping with CPU count, total/available RAM in bytes, OS name, and Python
        version.
    """
    memory = psutil.virtual_memory()
    logger.info("B09 Hardware diagnostics collected")
    return {
        "cpu_count": os.cpu_count() or 1,
        "memory_total_bytes": memory.total,
        "memory_available_bytes": memory.available,
        "system": platform.system(),
        "python_version": platform.python_version(),
    }


def create_pool(workers: int) -> ProcessPoolExecutor:
    """Construct an executor whose workers start when work is submitted.

    The configured HostSettings bounds explicit counts for Windows compatibility.
    This helper neither submits tasks nor loads quantitative providers.

    Args:
        workers: Explicit process count; zero selects CPU count minus one, bounded to
            1..61.

    Returns:
        A ProcessPoolExecutor owned and shut down by the caller.

    Raises:
        ValueError: The executor rejects a nonpositive explicit worker count.
    """
    count = workers or min(61, max(1, (os.cpu_count() or 1) - 1))
    logger.info("I04 Compute pool allocated with %s workers", count)
    return ProcessPoolExecutor(max_workers=count)
