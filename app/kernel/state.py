"""Persistent state ownership, namespace, and retention declarations."""

from dataclasses import dataclass
from enum import StrEnum


class RetentionPolicy(StrEnum):
    """Lifecycle retention policy for persistent state."""

    RETAIN = "retain"
    PURGE_ON_UNINSTALL = "purge_on_uninstall"


@dataclass(frozen=True, slots=True)
class StateDeclaration:
    """Declaration of persistent state owned by a feature.

    Attributes:
        namespace: Unique state namespace (e.g. 'data.historical_bars').
        schema_version: Version number for durable schema migrations.
        retention_policy: Lifecycle policy when feature is unloaded or uninstalled.
        description: Description of stored entities and files.
    """

    namespace: str
    schema_version: int = 1
    retention_policy: RetentionPolicy = RetentionPolicy.RETAIN
    description: str = ""

    def __post_init__(self) -> None:
        """Validate namespace format.

        Raises:
            ValueError: If namespace is empty or schema_version < 1.
        """
        if not self.namespace or not self.namespace.strip():
            msg = "State namespace must not be empty"
            raise ValueError(msg)
        if self.schema_version < 1:
            msg = f"schema_version must be >= 1, got {self.schema_version}"
            raise ValueError(msg)
