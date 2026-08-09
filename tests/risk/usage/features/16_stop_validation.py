"""Executable Risk stop-loss validation usage example.

Demonstrates FEAT-RISK-16 deterministic stop-loss side, tick, distance, loss, and widening checks.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.risk import (
    build_stop_validation,
    parse_stop_validation,
    validate_stop_loss,
)
from tests.risk._support import unwrap_risk_response

NOW = datetime(2026, 7, 19, tzinfo=UTC)


def _feature_header(title: str) -> None:
    """Print the feature header banner."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _format_result(obj: Any) -> str:
    """Dynamically format the output result type name and field/key signature."""
    if isinstance(obj, dict):
        return f"Output Result -> dict({', '.join(obj.keys())}) : dict"
    if isinstance(obj, tuple):
        return f"Output Result -> tuple[{len(obj)} results] : tuple"
    return f"Output Result -> {type(obj).__name__} : {type(obj).__name__}"


def _validation() -> dict[str, object]:
    """Build one bounded valid BUY stop-validation mapping."""
    return build_stop_validation(
        symbol="EURUSD",
        side="BUY",
        entry_price=Decimal("1.1000"),
        stop_price=Decimal("1.0950"),
        tick_size=Decimal("0.0001"),
        min_stop_distance=Decimal("0.0020"),
        contract_value=Decimal(100000),
        quantity=Decimal("0.1"),
        evaluated_at=NOW,
    )


def fr_risk_082() -> None:
    """FR-RISK-082: Build and parse a bounded StopValidation v1 contract."""
    _header("Stop-Loss Contract - Build/Parse StopValidation v1 (FR-RISK-082)")
    print("SUCCESS: FR-RISK-082")
    built = _validation()
    parsed = parse_stop_validation(built)
    print(_format_result(parsed))
    print(f"Data -> schema_id='{parsed['schema_id']}', symbol='{parsed['symbol']}'")


def fr_risk_083() -> None:
    """FR-RISK-083: Evaluate side, tick, invalidation, and noise distance checks."""
    _header("Stop-Loss Checks - Side/Tick/Distance/Loss (FR-RISK-083)")
    print("SUCCESS: FR-RISK-083")
    results = unwrap_risk_response(
        validate_stop_loss(_validation()), operation="validate_stop_loss"
    )
    print(_format_result(results))
    by_id = {item.limit_id: item.status.value for item in results}
    print(f"Data -> checks={by_id}")


def fr_risk_084() -> None:
    """FR-RISK-084: Block a looser stop than the previous one without widening permission."""
    _header("Stop-Loss Widening Permission - Block Without Permission (FR-RISK-084)")
    print("SUCCESS: FR-RISK-084")
    validation = build_stop_validation(
        symbol="EURUSD",
        side="BUY",
        entry_price=Decimal("1.1000"),
        stop_price=Decimal("1.0950"),
        tick_size=Decimal("0.0001"),
        min_stop_distance=Decimal("0.0020"),
        contract_value=Decimal(100000),
        quantity=Decimal("0.1"),
        evaluated_at=NOW,
        previous_stop_price=Decimal("1.0960"),
        allow_widening=False,
    )
    results = unwrap_risk_response(
        validate_stop_loss(validation), operation="validate_stop_loss"
    )
    widening = next(
        item for item in results if item.limit_id == "stop_widening_permission"
    )
    print(_format_result(widening))
    print(f"Data -> widening_status='{widening.status.value}'")


def main() -> None:
    """Run all feature examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-RISK-16 — stop_validation/ — Stop-Loss Validator\n\n"
        "Purpose: Deterministically validate stop-loss side, tick validity, invalidation "
        "distance, noise/venue floor, projected loss, and widening permission.\n\n"
        "Module flow:\n"
        "-> Build/parse the StopValidation v1 contract\n"
        "-> Evaluate side/tick/distance/loss checks\n"
        "-> Enforce widening permission"
    )
    fr_risk_082()
    fr_risk_083()
    fr_risk_084()


if __name__ == "__main__":
    main()
