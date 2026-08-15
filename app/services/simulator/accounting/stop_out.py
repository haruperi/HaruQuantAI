"""Account-mode and evidenced stop-out policy for Simulation."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import Decimal


def get_margin_state(
    *,
    equity: Decimal,
    used_margin: Decimal,
    margin_call_level: Decimal,
    stop_out_level: Decimal,
    mode: str,
) -> str:
    """Classify normal, margin-call, or stop-out account state.

    Returns:
        Canonical account threshold state.

    Raises:
        ValueError: If values or the provider threshold mode are invalid.
    """
    values = (equity, used_margin, margin_call_level, stop_out_level)
    if any(not value.is_finite() or value < 0 for value in values):
        raise ValueError("margin evidence is invalid")
    if mode == "PERCENT":
        level = Decimal("Infinity") if used_margin == 0 else equity / used_margin * 100
    elif mode == "MONEY":
        level = equity
    else:
        raise ValueError("stop-out mode is unsupported")
    if level <= stop_out_level:
        return "STOP_OUT"
    if level <= margin_call_level:
        return "MARGIN_CALL"
    return "NORMAL"


def plan_stop_out_liquidation(
    positions: Sequence[Mapping[str, object]],
    *,
    ordering: str,
    target_evidence_reference: str | None,
) -> tuple[str, ...]:
    """Return a target-evidenced deterministic liquidation sequence.

    Raises:
        ValueError: If canonical ordering lacks target-broker evidence.
    """
    if not target_evidence_reference:
        raise ValueError("canonical stop-out ordering requires target evidence")
    if ordering not in {"WORST_LOSS_FIRST", "OLDEST_FIRST"}:
        raise ValueError("stop-out ordering is not target-evidenced")

    def key(row: Mapping[str, object]) -> tuple[object, str]:
        """Return the target-evidenced stable ordering key."""
        primary: object = (
            Decimal(str(row["profit"]))
            if ordering == "WORST_LOSS_FIRST"
            else str(row["opened_at"])
        )
        return primary, str(row["position_id"])

    return tuple(str(row["position_id"]) for row in sorted(positions, key=key))


def project_account_mode(
    positions: Sequence[Mapping[str, object]],
    *,
    mode: str,
    symbol: str,
    side: str,
    volume: Decimal,
) -> tuple[Mapping[str, object], ...]:
    """Project netting or hedging position identity for one admitted fill.

    Returns:
        Detached projected position sequence.

    Raises:
        ValueError: If account mode, side, or volume is invalid.
    """
    if mode not in {"NETTING", "HEDGING"} or side not in {"BUY", "SELL"}:
        raise ValueError("account mode or side is unsupported")
    if not volume.is_finite() or volume <= 0:
        raise ValueError("fill volume must be positive")
    material = [dict(row) for row in positions]
    if mode == "HEDGING":
        material.append(
            {
                "position_id": f"hedge-{len(material) + 1}",
                "symbol": symbol,
                "side": side,
                "volume": volume,
            }
        )
        return tuple(material)
    existing = next((row for row in material if row.get("symbol") == symbol), None)
    if existing is None:
        return (
            {
                "position_id": f"net-{symbol}",
                "symbol": symbol,
                "side": side,
                "volume": volume,
            },
        )
    signed = Decimal(str(existing["volume"])) * (1 if existing["side"] == side else -1)
    total = signed + volume
    if total == 0:
        return tuple(row for row in material if row is not existing)
    existing["side"] = side if total > 0 else ("SELL" if side == "BUY" else "BUY")
    existing["volume"] = abs(total)
    return tuple(material)


__all__ = ["get_margin_state", "plan_stop_out_liquidation", "project_account_mode"]
