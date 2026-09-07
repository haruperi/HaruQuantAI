"""Universal standard operation response envelope across all domains."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class StandardResponse[T]:
    """Standard operation response envelope across all domain operations."""

    status: str = "success"
    data: T | None = None
    error: object | None = None
    message: str = ""
    operation: str = ""
    metadata: dict[str, object] = field(default_factory=dict)
    execution_time_ms: float = 0.0

    def to_dict(self) -> dict[str, object]:
        """Convert the response to a standard dictionary.

        Returns:
            Dictionary representation of the response envelope.
        """
        return asdict(self)

    def __getitem__(self, item: str) -> object:
        """Allow dict-style key access for backward compatibility.

        Args:
            item: Field name to access.

        Returns:
            Field value if present.

        Raises:
            KeyError: If item is not an attribute of the response.
        """
        if hasattr(self, item):
            return getattr(self, item)
        raise KeyError(item)

    def __contains__(self, item: object) -> bool:
        """Allow 'key in response' checks.

        Args:
            item: Key name to check.

        Returns:
            True if key is an attribute of the response.
        """
        return isinstance(item, str) and hasattr(self, item)

    def get(self, item: str, default: object = None) -> object:
        """Allow dict-style .get() access.

        Args:
            item: Key name to access.
            default: Default value if key is not found.

        Returns:
            Field value if present, otherwise default.
        """
        return getattr(self, item, default)
