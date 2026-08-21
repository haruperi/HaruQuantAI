"""Typed outcome model for transactional feature replacement."""

from dataclasses import dataclass
from enum import StrEnum


class ReplacementStatus(StrEnum):
    """Final state of a replacement attempt."""

    ROLLED_BACK = "ROLLED_BACK"
    COMMITTED = "COMMITTED"
    COMMITTED_DEGRADED = "COMMITTED_DEGRADED"


@dataclass(frozen=True, slots=True)
class ReplacementReport:
    """Truthful replacement result separating rollback from cleanup degradation."""

    feature_id: str
    old_generation: int | None
    new_generation: int | None
    committed: bool
    rolled_back: bool
    cleanup_errors: tuple[str, ...]
    status: ReplacementStatus
    zero_downtime: bool = False

    @property
    def message(self) -> str | None:
        """Return a compact compatibility message when cleanup or rollback failed."""
        return "; ".join(self.cleanup_errors) if self.cleanup_errors else None

    def __iter__(self):
        """Preserve legacy two-value unpacking as ``committed, message``."""
        yield self.committed
        yield self.message
