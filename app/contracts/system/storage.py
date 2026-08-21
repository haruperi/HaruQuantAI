"""Persistent key-value and binary storage capability contract."""

from typing import Protocol, runtime_checkable

from app.kernel.capability import CapabilityKey


@runtime_checkable
class StorageEngine(Protocol):
    """Protocol for underlying key-value or document persistence."""

    async def get(self, key: str) -> bytes | None:
        """Retrieve binary content for a given key.

        Args:
            key: Unique key identifier.

        Returns:
            Binary payload if found, None otherwise.
        """
        ...

    async def set(self, key: str, value: bytes) -> None:
        """Store binary content for a given key.

        Args:
            key: Unique key identifier.
            value: Binary payload to persist.
        """
        ...

    async def delete(self, key: str) -> bool:
        """Delete stored content for a given key.

        Args:
            key: Unique key identifier.

        Returns:
            True if the key was deleted, False if not found.
        """
        ...

    async def list_keys(self, prefix: str = "") -> tuple[str, ...]:
        """List all stored keys optionally matching prefix.

        Args:
            prefix: Optional key prefix filter.

        Returns:
            Tuple of matching keys.
        """
        ...

    def partition(self, namespace: str) -> StorageEngine:
        """Return a scoped StorageEngine isolated to a sub-namespace.

        Args:
            namespace: Sub-namespace identifier.

        Returns:
            Isolated StorageEngine partition.
        """
        ...


SYSTEM_STORAGE = CapabilityKey[StorageEngine](
    name="system.storage",
    major=1,
)
