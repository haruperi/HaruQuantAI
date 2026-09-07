"""Atomic process-local writer fencing for one workspace."""

from __future__ import annotations

import json
import os
import uuid
from collections.abc import Callable
from pathlib import Path

from app.composition.logging import get_logger
from app.contracts.workspace.errors import WorkspaceAlreadyOpenError
from app.contracts.workspace.models import WorkspaceWriterFence

STILL_ACTIVE = 259
logger = get_logger(__name__)


def is_process_alive(pid: int) -> bool:
    """Return whether a process identifier currently represents a live process."""
    if pid <= 0:
        return False
    try:
        import ctypes

        windll = getattr(ctypes, "windll", None)
        if windll is not None:
            handle = windll.kernel32.OpenProcess(0x1000, False, pid)
            if handle == 0:
                return False
            exit_code = ctypes.c_ulong()
            windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code))
            windll.kernel32.CloseHandle(handle)
            return bool(exit_code.value == STILL_ACTIVE)
        os.kill(pid, 0)
        return True
    except AttributeError, OSError:
        return False


def acquire_writer_fence(
    root: Path,
    workspace_id: str,
    timestamp: str,
    *,
    read_only: bool,
    process_alive: Callable[[int], bool] = is_process_alive,
) -> WorkspaceWriterFence:
    """Acquire an exclusive filesystem fence without an overwrite race.

    Returns:
        A writer-owned or explicit read-only fence.

    Raises:
        WorkspaceAlreadyOpenError: If a live writer owns the workspace.
    """
    if read_only:
        logger.info(
            "Workspace read-only fence admitted",
            event="workspace.fence.read_only_admitted",
            workspace_id=workspace_id,
        )
        return WorkspaceWriterFence(
            workspace_id=workspace_id,
            lock_token=f"read_only_{uuid.uuid4()}",
            holder_pid=os.getpid(),
            acquired_at=timestamp,
            is_write_locked=False,
            is_read_only=True,
        )
    lock_path = root / ".workspace.lock"
    token = str(uuid.uuid4())
    payload = {
        "workspace_id": workspace_id,
        "holder_pid": os.getpid(),
        "lock_token": token,
        "acquired_at": timestamp,
    }
    encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
    for _attempt in range(2):
        try:
            descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            try:
                os.write(descriptor, encoded)
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
            logger.info(
                "Workspace writer fence acquired",
                event="workspace.fence.acquired",
                workspace_id=workspace_id,
            )
            return WorkspaceWriterFence(
                workspace_id=workspace_id,
                lock_token=token,
                holder_pid=os.getpid(),
                acquired_at=timestamp,
                is_write_locked=True,
                is_read_only=False,
            )
        except FileExistsError:
            try:
                current = json.loads(lock_path.read_text(encoding="utf-8"))
                holder_pid = int(current.get("holder_pid", 0))
            except OSError, ValueError, json.JSONDecodeError:
                holder_pid = 0
            if process_alive(holder_pid):
                logger.warning(
                    "Workspace writer fence denied",
                    event="workspace.fence.denied",
                    workspace_id=workspace_id,
                )
                raise WorkspaceAlreadyOpenError(
                    holder_pid=holder_pid,
                    lock_file=str(lock_path),
                ) from None
            try:
                lock_path.unlink()
            except FileNotFoundError:
                continue
    raise WorkspaceAlreadyOpenError(lock_file=str(lock_path))


def release_writer_fence(root: Path, token: str) -> bool:
    """Release a fence only when the caller presents the exact secret token.

    Returns:
        Whether the matching fence existed and was removed.
    """
    lock_path = root / ".workspace.lock"
    try:
        payload = json.loads(lock_path.read_text(encoding="utf-8"))
    except FileNotFoundError, OSError, ValueError, json.JSONDecodeError:
        return False
    if payload.get("lock_token") != token:
        logger.warning(
            "Workspace writer fence release denied",
            event="workspace.fence.release_denied",
            reason="token_mismatch",
        )
        return False
    try:
        lock_path.unlink()
    except FileNotFoundError:
        return False
    logger.info("Workspace writer fence released", event="workspace.fence.released")
    return True
