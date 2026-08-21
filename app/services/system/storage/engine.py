"""Durable disk-backed storage engine with partition isolation."""

import asyncio
from pathlib import Path
from typing import override

from app.contracts.system.storage import StorageEngine


class DiskStorageEngine(StorageEngine):
    """File-system backed persistent storage engine with atomic operations.

    Satisfies:
        FR-SYS-STORE_PERSISTENT_DATA: Persists binary payloads durably.
        FR-SYS-RETRIEVE_PERSISTENT_DATA: Retrieves binary payloads by key.
        FR-SYS-PURGE_NAMESPACE_DATA: Deletes stored keys and purges namespaces.
    """

    def __init__(self, directory: Path) -> None:
        """Initialize engine with dedicated filesystem directory.

        Args:
            directory: Root directory path for this storage partition.
        """
        self._dir = directory
        self._lock = asyncio.Lock()

    @property
    def directory(self) -> Path:
        """Return partition directory path."""
        return self._dir

    def _ensure_dir(self) -> None:
        """Ensure storage directory exists."""
        self._dir.mkdir(parents=True, exist_ok=True)

    def _key_path(self, key: str) -> Path:
        """Compute safe file path for key.

        Args:
            key: Unique key identifier.

        Returns:
            Computed target Path on filesystem.
        """
        safe_key = key.replace("/", "_").replace("\\", "_")
        return self._dir / f"{safe_key}.dat"

    @override
    async def get(self, key: str) -> bytes | None:
        """Retrieve binary content for a given key.

        Args:
            key: Unique key identifier.

        Returns:
            Binary payload if found, None otherwise.
        """
        target = self._key_path(key)
        if not target.is_file():
            return None
        return await asyncio.to_thread(target.read_bytes)

    @override
    async def set(self, key: str, value: bytes) -> None:
        """Store binary content atomically for a given key.

        Args:
            key: Unique key identifier.
            value: Binary payload to persist.
        """
        async with self._lock:
            await asyncio.to_thread(self._ensure_dir)
            target = self._key_path(key)
            temp = target.with_suffix(".tmp")
            await asyncio.to_thread(temp.write_bytes, value)
            await asyncio.to_thread(temp.replace, target)

    @override
    async def delete(self, key: str) -> bool:
        """Delete stored content for a given key.

        Args:
            key: Unique key identifier.

        Returns:
            True if the key was deleted, False if not found.
        """
        async with self._lock:
            target = self._key_path(key)
            if not target.is_file():
                return False
            await asyncio.to_thread(target.unlink, True)
            return True

    @override
    async def list_keys(self, prefix: str = "") -> tuple[str, ...]:
        """List all stored keys matching optional prefix.

        Args:
            prefix: Optional key prefix filter.

        Returns:
            Tuple of matching keys.
        """
        if not self._dir.is_dir():
            return ()

        def _scan() -> tuple[str, ...]:
            keys: list[str] = []
            for item in self._dir.glob("*.dat"):
                if item.is_file():
                    key = item.stem
                    if not prefix or key.startswith(prefix):
                        keys.append(key)
            return tuple(sorted(keys))

        return await asyncio.to_thread(_scan)

    @override
    def partition(self, namespace: str) -> StorageEngine:
        """Return an isolated storage engine partition under a sub-namespace.

        Args:
            namespace: Sub-namespace directory name.

        Returns:
            Isolated DiskStorageEngine instance.
        """
        safe_ns = namespace.replace("..", "").replace("/", "_").replace("\\", "_")
        partition_dir = self._dir / safe_ns
        return DiskStorageEngine(partition_dir)
