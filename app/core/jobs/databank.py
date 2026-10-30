"""Background databank operations with transactional safety and cancellation."""

from __future__ import annotations

import json
import threading
from collections.abc import Generator, Sequence
from contextlib import contextmanager
from pathlib import Path

from app.core.host.logging import get_logger
from app.core.host.persistence import HostPersistence
from app.core.jobs.manager import JobContext
from app.core.lib.errors import DomainError
from app.core.trading.results.contracts import RunResult
from app.core.trading.results.store import ResultStore

logger = get_logger(__name__)

_DATABANK_LOCKS: set[str] = set()
_LOCKS_MUTEX = threading.Lock()


def lock_databank(databank_id: str) -> None:
    """Lock a databank to prevent modifications."""
    with _LOCKS_MUTEX:
        _DATABANK_LOCKS.add(databank_id)


def unlock_databank(databank_id: str) -> None:
    """Unlock a databank to allow modifications."""
    with _LOCKS_MUTEX:
        _DATABANK_LOCKS.discard(databank_id)


def is_databank_locked(databank_id: str) -> bool:
    """Check whether a databank is currently locked."""
    with _LOCKS_MUTEX:
        return databank_id in _DATABANK_LOCKS


def clear_databank_locks() -> None:
    """Clear all active databank locks."""
    with _LOCKS_MUTEX:
        _DATABANK_LOCKS.clear()


@contextmanager
def locked_databank(databank_id: str) -> Generator[None]:
    """Context manager to temporarily lock a databank."""
    lock_databank(databank_id)
    try:
        yield
    finally:
        unlock_databank(databank_id)


class AddToDatabankJob:
    """Callable job that stages and inserts backtest results into a databank."""

    def __init__(
        self,
        databank_id: str,
        results: Sequence[RunResult],
        store: ResultStore | None = None,
    ) -> None:
        self.databank_id = str(databank_id)
        self.results = tuple(results)
        self.store = store or ResultStore(HostPersistence())
        self.progress: float = 0.0
        self.step_message: str = ""

    def __call__(self, context: JobContext | None = None) -> int:
        """Execute insertion of candidate results into target databank."""
        if is_databank_locked(self.databank_id):
            raise DomainError(
                code="DATABANK_LOCKED",
                message=f"Databank '{self.databank_id}' is locked",
                details={"databank_id": self.databank_id},
            )

        if not self.results:
            self.progress = 1.0
            self.step_message = "Complete: no items to add"
            if context is not None:
                context.report_progress(100.0, self.step_message)
            return 0

        total = len(self.results)
        with self.store.persistence.transaction() as tx:
            tx_store = type(self.store)(tx)
            for idx, res in enumerate(self.results):
                if context is not None:
                    context.raise_if_cancelled()

                tx_store.save_result(self.databank_id, res)
                self.progress = (idx + 1) / total
                self.step_message = (
                    f"Added {idx + 1}/{total} to databank '{self.databank_id}'"
                )
                logger.info(self.step_message)
                if context is not None:
                    context.report_progress(
                        round(self.progress * 100.0, 2), self.step_message
                    )

        return total


class DeleteFromDatabankJob:
    """Callable job that atomically deletes backtest results from a databank."""

    def __init__(
        self,
        databank_id: str,
        result_ids: Sequence[str],
        store: ResultStore | None = None,
    ) -> None:
        self.databank_id = str(databank_id)
        self.result_ids = tuple(result_ids)
        self.store = store or ResultStore(HostPersistence())
        self.progress: float = 0.0
        self.step_message: str = ""

    def __call__(self, context: JobContext | None = None) -> int:
        """Execute atomic deletion of specified results."""
        if is_databank_locked(self.databank_id):
            raise DomainError(
                code="DATABANK_LOCKED",
                message=f"Databank '{self.databank_id}' is locked",
                details={"databank_id": self.databank_id},
            )

        if not self.result_ids:
            self.progress = 1.0
            self.step_message = "Complete: no items to delete"
            if context is not None:
                context.report_progress(100.0, self.step_message)
            return 0

        total = len(self.result_ids)
        deleted_count = 0
        with self.store.persistence.transaction() as tx:
            tx_store = type(self.store)(tx)
            for idx, rid in enumerate(self.result_ids):
                if context is not None:
                    context.raise_if_cancelled()

                removed = tx_store.delete_result(rid)
                if removed:
                    deleted_count += 1
                self.progress = (idx + 1) / total
                self.step_message = (
                    f"Deleted {idx + 1}/{total} from databank '{self.databank_id}'"
                )
                logger.info(self.step_message)
                if context is not None:
                    context.report_progress(
                        round(self.progress * 100.0, 2), self.step_message
                    )

        return deleted_count


class MoveToDatabankJob:
    """Callable job that moves candidate results transactionally across databanks."""

    def __init__(
        self,
        source_databank_id: str,
        target_databank_id: str,
        result_ids: Sequence[str],
        store: ResultStore | None = None,
    ) -> None:
        self.source_databank_id = str(source_databank_id)
        self.target_databank_id = str(target_databank_id)
        self.result_ids = tuple(result_ids)
        self.store = store or ResultStore(HostPersistence())
        self.progress: float = 0.0
        self.step_message: str = ""

    def _load_candidates(self, context: JobContext | None) -> list[RunResult]:
        """Validate and fetch all candidate results from source databank."""
        candidates: list[RunResult] = []
        for rid in self.result_ids:
            if context is not None:
                context.raise_if_cancelled()
            res = self.store.get_result(rid)
            if res.databank_id != self.source_databank_id:
                raise DomainError(
                    code="RESULT_NOT_IN_SOURCE",
                    message=(
                        f"Result '{rid}' is in databank '{res.databank_id}', "
                        f"not source '{self.source_databank_id}'"
                    ),
                    details={
                        "result_id": rid,
                        "source_databank_id": self.source_databank_id,
                        "actual_databank_id": res.databank_id,
                    },
                )
            candidates.append(res)
        return candidates

    def __call__(self, context: JobContext | None = None) -> int:
        """Execute transactional copy-then-delete across databanks."""
        if is_databank_locked(self.source_databank_id):
            raise DomainError(
                code="DATABANK_LOCKED",
                message=f"Source databank '{self.source_databank_id}' is locked",
                details={"databank_id": self.source_databank_id},
            )
        if is_databank_locked(self.target_databank_id):
            raise DomainError(
                code="DATABANK_LOCKED",
                message=f"Target databank '{self.target_databank_id}' is locked",
                details={"databank_id": self.target_databank_id},
            )

        if not self.result_ids:
            self.progress = 1.0
            self.step_message = "Complete: no items to move"
            if context is not None:
                context.report_progress(100.0, self.step_message)
            return 0

        candidates = self._load_candidates(context)
        total = len(candidates)
        with self.store.persistence.transaction() as tx:
            tx_store = type(self.store)(tx)
            for idx, res in enumerate(candidates):
                if context is not None:
                    context.raise_if_cancelled()

                # Move to target databank by updating record's databank_id
                tx_store.save_result(self.target_databank_id, res)

                self.progress = (idx + 1) / total
                self.step_message = (
                    f"Moved {idx + 1}/{total} from '{self.source_databank_id}' "
                    f"to '{self.target_databank_id}'"
                )
                logger.info(self.step_message)
                if context is not None:
                    context.report_progress(
                        round(self.progress * 100.0, 2), self.step_message
                    )

        return total


class LoadFileToDatabankJob:
    """Callable job that parses an exported result file and imports into a databank."""

    def __init__(
        self,
        databank_id: str,
        file_path: Path | str,
        store: ResultStore | None = None,
    ) -> None:
        self.databank_id = str(databank_id)
        self.file_path = Path(file_path)
        self.store = store or ResultStore(HostPersistence())
        self.progress: float = 0.0
        self.step_message: str = ""

    def _parse_file(self) -> list[RunResult]:
        """Read and parse results from JSON file path."""
        if not self.file_path.exists():
            raise DomainError(
                code="FILE_NOT_FOUND",
                message=f"Result file '{self.file_path}' does not exist",
                details={"file_path": str(self.file_path)},
            )

        try:
            raw_content = self.file_path.read_text(encoding="utf-8")
            data = json.loads(raw_content)
        except (OSError, json.JSONDecodeError) as err:
            raise DomainError(
                code="INVALID_FILE_FORMAT",
                message=f"Could not parse result file '{self.file_path}': {err}",
                details={"file_path": str(self.file_path)},
            ) from err

        results: list[RunResult] = []
        if isinstance(data, dict):
            if "results" in data and isinstance(data["results"], list):
                results.extend(
                    RunResult.from_dict(item)
                    for item in data["results"]
                    if isinstance(item, dict)
                )
            else:
                results.append(RunResult.from_dict(data))
        elif isinstance(data, list):
            results.extend(
                RunResult.from_dict(item) for item in data if isinstance(item, dict)
            )
        else:
            raise DomainError(
                code="INVALID_FILE_FORMAT",
                message="File content must be a JSON object or array of objects",
                details={"file_path": str(self.file_path)},
            )
        return results

    def __call__(self, context: JobContext | None = None) -> int:
        """Parse result file and import candidates into target databank."""
        if is_databank_locked(self.databank_id):
            raise DomainError(
                code="DATABANK_LOCKED",
                message=f"Databank '{self.databank_id}' is locked",
                details={"databank_id": self.databank_id},
            )

        results = self._parse_file()
        if not results:
            self.progress = 1.0
            self.step_message = "Complete: no valid records found in file"
            if context is not None:
                context.report_progress(100.0, self.step_message)
            return 0

        total = len(results)
        with self.store.persistence.transaction() as tx:
            tx_store = type(self.store)(tx)
            for idx, res in enumerate(results):
                if context is not None:
                    context.raise_if_cancelled()

                tx_store.save_result(self.databank_id, res)
                self.progress = (idx + 1) / total
                self.step_message = (
                    f"Imported {idx + 1}/{total} from '{self.file_path.name}' "
                    f"into databank '{self.databank_id}'"
                )
                logger.info(self.step_message)
                if context is not None:
                    context.report_progress(
                        round(self.progress * 100.0, 2), self.step_message
                    )

        return total


__all__ = [
    "AddToDatabankJob",
    "DeleteFromDatabankJob",
    "LoadFileToDatabankJob",
    "MoveToDatabankJob",
    "clear_databank_locks",
    "is_databank_locked",
    "lock_databank",
    "locked_databank",
    "unlock_databank",
]
