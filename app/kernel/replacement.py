"""Replacement report models and status definitions for transactional feature swaps."""

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class ReplacementReport:
    """Diagnostic report detailing the outcome of a transactional feature replacement.

    Attributes:
        feature_id: Unique identifier of the replaced feature.
        old_generation: Capability generation number prior to replacement.
        new_generation: Capability generation number following replacement.
        committed: Whether the replacement was committed to the active registry.
        rolled_back: Whether the replacement was rolled back to the old provider.
        cleanup_errors: Tuple of error messages encountered during disposal.
        status: Outcome classification ('committed', 'rolled_back', 'degraded').
        error: Failure message if pre-commit or health-check failed.
    """

    feature_id: str
    old_generation: int
    new_generation: int
    committed: bool
    rolled_back: bool
    cleanup_errors: tuple[str, ...] = field(default_factory=tuple)
    status: str = "committed"
    error: str | None = None
