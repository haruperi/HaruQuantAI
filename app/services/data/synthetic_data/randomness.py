"""Seed requirement for deterministic synthetic generation."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.data.synthetic_data.contracts import SyntheticRequest


def require_seed(request: SyntheticRequest) -> int:
    """Return the request seed, failing when deterministic replay is impossible."""
    if request.seed is None:
        raise ValueError("synthetic generation requires a seed")
    return request.seed


__all__ = ["require_seed"]
