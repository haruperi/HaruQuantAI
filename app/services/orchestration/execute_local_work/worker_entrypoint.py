"""Spawn-importable worker entrypoint with no import-time side effects."""

from __future__ import annotations

import hashlib
from multiprocessing.synchronize import Event
from multiprocessing.queues import Queue
from multiprocessing import shared_memory


def run_worker(operation_id: str, shm_name: str, byte_count: int, expected_hash: str, seed: int, cancel: Event, output: Queue) -> None:
    """Execute one bounded built-in operation and return a serializable result."""
    shm = shared_memory.SharedMemory(name=shm_name)
    try:
        data = bytes(shm.buf[:byte_count])
        if hashlib.sha256(data).hexdigest() != expected_hash:
            output.put(("FAILED", b"", "INPUT_HASH_MISMATCH")); return
        if cancel.is_set():
            output.put(("CANCELLED", b"", "CANCELLED_BEFORE_START")); return
        if operation_id == "sha256":
            digest = hashlib.sha256()
            for offset in range(0, len(data), 1024 * 1024):
                if cancel.is_set():
                    output.put(("CANCELLED", b"", "CANCELLED")); return
                digest.update(data[offset: offset + 1024 * 1024])
            result = digest.hexdigest().encode()
        elif operation_id == "echo":
            result = data
        else:
            output.put(("FAILED", b"", "OPERATION_NOT_REGISTERED")); return
        output.put(("COMPLETED", result, ""))
    finally:
        shm.close()
