"""Result models for transactional feature replacement."""

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class ReplacementReport:
    """Describe commit, rollback, consumer remount, and cleanup outcomes."""

    feature_id: str
    old_generation: int
    new_generation: int
    committed: bool
    rolled_back: bool
    cleanup_errors: tuple[str, ...] = field(default_factory=tuple)
    consumer_errors: tuple[str, ...] = field(default_factory=tuple)
    status: str = "committed"
    error: str | None = None

    @property
    def is_degraded(self) -> bool:
        """Return whether replacement committed with unresolved problems."""
        return self.status == "degraded"
