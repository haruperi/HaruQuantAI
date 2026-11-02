"""Offline migration of SQ storage directories and host-owned dataset references.

Description:
    Preflight an offline workspace, back up its database/files, rename only the two
    approved market folders and update references through HostPersistence. Roll back
    directory moves if the host transaction fails. No SQL or provider IDs are changed.
Purpose:
    FEAT-MARKET-FOLDER-RENAME: preserve market data while adopting equity/futures names.
Key Capabilities:
    - FR-MARKET-FOLDER-RENAME-offline-migration: reject running hosts, collisions and
      linked paths; verify file hashes and retain backups. INFO logs migration results;
      WARNING logs rollback; temporary-store tests explicitly verify both.
Python API Usage:
    migrate(Path(project_root))
CLI Usage:
    uv run python -m scripts.rename_sq_market_folders --apply
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import uuid
from pathlib import Path
from typing import Any

import psutil
from app.core.data.market_storage import provider_storage_name
from app.core.host.logging import get_logger
from app.core.host.persistence import HostPersistence

logger = get_logger(__name__)
RENAMES = {"sq_equity": "equity", "sq_futures": "futures"}


def require(response: dict[str, Any]) -> Any:
    """Fail closed on any host persistence error."""
    if not response["success"]:
        raise RuntimeError("Host persistence rejected the folder migration operation")
    return response["data"]


def ensure_offline() -> None:
    """Refuse migration while a Python app host process is running."""
    for process in psutil.process_iter(["cmdline"]):
        arguments = process.info["cmdline"] or []
        if "app.main" in arguments or any("uvicorn" in value for value in arguments):
            raise RuntimeError("Stop the app host before renaming market folders")


def manifest(root: Path) -> dict[str, str]:
    """Hash regular files, rejecting links and paths outside the approved root."""
    result = {}
    for item in [root, *root.rglob("*")]:
        if (
            item.is_symlink()
            or item.is_junction()
            or not item.resolve().is_relative_to(root)
        ):
            raise ValueError("Linked or escaping paths are not allowed in migration")
        if item.name.endswith(".publication.json"):
            raise ValueError("Recover pending publications before migration")
        if item.is_file():
            with item.open("rb") as stream:
                result[str(item.relative_to(root))] = hashlib.file_digest(
                    stream, "sha256"
                ).hexdigest()
    return result


def rewrite(value: Any, moves: list[tuple[Path, Path]], project: Path) -> Any:
    """Rewrite only path strings contained within approved old directories."""
    if isinstance(value, dict):
        return {key: rewrite(item, moves, project) for key, item in value.items()}
    if isinstance(value, list):
        return [rewrite(item, moves, project) for item in value]
    if not isinstance(value, str) or not value:
        return value
    normalized = value.replace("\\", "/").casefold()
    prefixes = [str(old).replace("\\", "/").casefold() for old, _ in moves]
    prefixes += [
        str(old.relative_to(project)).replace("\\", "/").casefold() for old, _ in moves
    ]
    if not any(
        normalized == prefix or normalized.startswith(prefix + "/")
        for prefix in prefixes
    ):
        return value
    path = Path(value)
    absolute = (path if path.is_absolute() else project / path).resolve()
    for old, new in moves:
        if absolute.is_relative_to(old):
            updated = new / absolute.relative_to(old)
            return str(updated if path.is_absolute() else updated.relative_to(project))
    return value


def records(gateway: HostPersistence) -> list[dict[str, Any]]:
    """Read every dataset through bounded host-owned pages."""
    result: list[dict[str, Any]] = []
    while True:
        page = require(
            gateway.read_records("datamgr_datasets", limit=1000, offset=len(result))
        )["records"]
        result.extend(page)
        if len(page) < 1000:
            return result


def backup_files(database: Path, backup: Path, moves: list[tuple[Path, Path]]) -> None:
    """Copy quiescent database files and approved trees while writers are locked."""
    for suffix in ("", "-wal"):
        source = Path(str(database) + suffix)
        if source.exists():
            shutil.copy2(source, backup / source.name)
    for old, _ in moves:
        shutil.copytree(old, backup / old.name)


def verify_files(root: Path, expected: dict[str, str]) -> None:
    """Reject changed contents before committing migrated metadata."""
    if manifest(root) != expected:
        raise RuntimeError("File verification failed after folder rename")


def migrate(project_root: Path) -> Path:
    """Back up, migrate and verify folder contents in an offline workspace."""
    ensure_offline()
    project = project_root.resolve(strict=True)
    market = project / "data" / "market"
    if market.resolve() != market:
        raise ValueError("Market root must not contain linked paths")
    moves = [(market / old, market / provider_storage_name(old)) for old in RENAMES]
    for old, new in moves:
        if not old.is_dir() or new.exists():
            raise FileExistsError(
                "Old folders must exist and destinations must be absent"
            )
    hashes = {old.name: manifest(old) for old, _ in moves}
    database = project / "data" / "database" / "haruquantai.db"
    if database.resolve() != database or not database.is_file():
        raise ValueError("Expected an existing local host database")
    backup = (
        project.parent
        / (project.name + "-backups")
        / ("market-folder-rename-" + uuid.uuid4().hex)
    )
    backup.mkdir(parents=True)
    gateway = HostPersistence(database)
    completed: list[tuple[Path, Path]] = []
    try:
        with gateway.transaction() as transaction:
            before = records(transaction)
            backup_files(database, backup, moves)
            (backup / "manifest.json").write_text(
                json.dumps({"files": hashes, "datasets": before}, indent=2),
                encoding="utf-8",
            )
            for old, new in moves:
                old.rename(new)
                completed.append((old, new))
                verify_files(new, hashes[old.name])
            for row in before:
                values = {
                    "path": rewrite(row["path"], moves, project),
                    "lineage_json": json.dumps(
                        rewrite(json.loads(row["lineage_json"]), moves, project)
                    ),
                }
                if values["path"] != row["path"] or json.loads(
                    values["lineage_json"]
                ) != json.loads(row["lineage_json"]):
                    require(
                        transaction.update_record(
                            "datamgr_datasets", values, filters={"id": row["id"]}
                        )
                    )
    except BaseException:
        for old, new in reversed(completed):
            new.rename(old)
        logger.warning(
            "FR-MARKET-FOLDER-RENAME-offline-migration: rolled back directory moves"
        )
        raise
    logger.info(
        "FR-MARKET-FOLDER-RENAME-offline-migration: migrated %d folders; backup=%s",
        len(moves),
        backup,
    )
    return backup


def main() -> None:
    """Apply only when the operator explicitly supplies the apply flag."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", required=True)
    parser.parse_args()
    migrate(Path(__file__).resolve().parents[1])


if __name__ == "__main__":
    main()
