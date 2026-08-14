"""Function-only feature API for the parity envelope and comparator."""

from __future__ import annotations

from app.services.simulator.parity.compare import compare_parity_evidence
from app.services.simulator.parity.envelope import (
    get_parity_envelope,
    get_parity_maturity_ladder,
)
from app.services.simulator.parity.normalize import normalize_parity_evidence

__all__ = [
    "compare_parity_evidence",
    "get_parity_envelope",
    "get_parity_maturity_ladder",
    "normalize_parity_evidence",
]
