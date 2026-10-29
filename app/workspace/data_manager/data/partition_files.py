"""Dataset writer locks and recoverable replacement of canonical Parquet files."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import tempfile
import time
import uuid
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from app.core.host.persistence import HostPersistence


def canonical_target(stage: Path) -> Path:
    """Map a private staged file to its yearly/monthly canonical filename."""
    return stage.with_name(f"{stage.name.split('.')[1]}.parquet")


@contextmanager
def dataset_lock(root: Path, context: Any = None) -> Generator[None]:
    """Serialize dataset writers across processes without holding a SQLite lock."""
    locks = Path(tempfile.gettempdir()) / "haruquantai-market-locks"
    locks.mkdir(exist_ok=True)
    name = hashlib.sha256(str(root.resolve()).casefold().encode()).hexdigest()
    with (locks / name).open("a+b") as stream:
        stream.write(b"0")
        stream.flush()
        while True:
            if context is not None:
                context.wait_if_paused()
                context.raise_if_cancelled()
            try:
                stream.seek(0)
                if sys.platform == "win32":
                    import msvcrt

                    msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError, PermissionError:
                time.sleep(0.05)
        try:
            yield
        finally:
            stream.seek(0)
            if sys.platform == "win32":
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


class FilePublication:
    """Keep a durable undo journal until the catalog commit has succeeded."""

    def __init__(
        self, root: Path, stages: list[Path], dataset_id: str, token: str
    ) -> None:
        self.journal = root / f".{uuid.uuid4().hex}.publication.json"
        self.data: dict[str, Any] = {
            "dataset_id": dataset_id,
            "token": token,
            "files": [
                {
                    "stage": str(stage),
                    "target": str(canonical_target(stage)),
                    "backup": str(stage.with_suffix(".backup"))
                    if canonical_target(stage).exists()
                    else None,
                }
                for stage in stages
            ],
        }

    def prepare(self) -> None:
        """Copy undo files and flush the journal outside the SQLite transaction."""
        for item in self.data["files"]:
            if item["backup"]:
                shutil.copy2(item["target"], item["backup"])
                with Path(item["backup"]).open("rb+") as stream:
                    os.fsync(stream.fileno())
        temporary = self.journal.with_suffix(".json.tmp")
        with temporary.open("w", encoding="utf-8") as stream:
            json.dump(self.data, stream)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(self.journal)

    def install(self) -> None:
        """Atomically replace prepared files without copying under a database lock."""
        if not self.journal.exists():
            self.prepare()
        for item in self.data["files"]:
            Path(item["stage"]).replace(item["target"])

    def rollback(self) -> None:
        """Restore the prior generation on replacement or catalog failure."""
        for item in self.data["files"]:
            backup = Path(item["backup"]) if item["backup"] else None
            if backup is not None and backup.exists():
                backup.replace(item["target"])
            elif backup is None and not Path(item["stage"]).exists():
                Path(item["target"]).unlink(missing_ok=True)
        self.finish()

    def finish(self) -> None:
        """Remove the undo journal and temporary files after successful resolution."""
        self.journal.unlink(missing_ok=True)
        self.journal.with_suffix(".json.tmp").unlink(missing_ok=True)
        for item in self.data["files"]:
            Path(item["stage"]).unlink(missing_ok=True)
            if item["backup"]:
                Path(item["backup"]).unlink(missing_ok=True)


def recover_publications(root: Path, gateway: HostPersistence) -> None:
    """Resolve journals left by a terminated writer; caller holds dataset lock."""
    for journal in root.glob(".*.publication.json"):
        data = json.loads(journal.read_text(encoding="utf-8"))
        for item in data["files"]:
            for key in ("stage", "target", "backup"):
                if item[key] and not Path(item[key]).resolve().is_relative_to(root):
                    raise ValueError("Publication journal path escapes dataset root")
        result = gateway.read_records(
            "datamgr_datasets",
            filters={"id": data["dataset_id"]},
            limit=1,
        )
        if not result["success"]:
            raise RuntimeError("Cannot recover partition publication")
        rows = result["data"]["records"]
        publication = FilePublication(root, [], data["dataset_id"], data["token"])
        publication.journal, publication.data = journal, data
        if rows and rows[0]["updated_at"] == data["token"]:
            publication.finish()
        else:
            publication.rollback()


def recover_catalog_publications(gateway: HostPersistence) -> None:
    """Recover interrupted canonical replacements before the backend serves reads."""
    offset = 0
    while True:
        result = gateway.read_records("datamgr_datasets", offset=offset)
        if not result["success"]:
            return  # A fresh installation may not have a dataset catalog yet.
        rows = result["data"]["records"]
        if not rows:
            return
        for row in rows:
            root = Path(row["path"]).resolve()
            if root.is_dir() and any(root.glob(".*.publication.json")):
                with dataset_lock(root):
                    recover_publications(root, gateway)
        offset += len(rows)
