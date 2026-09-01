"""Evidence-bound broker-server rollover and swap calculations."""

# ruff: noqa: DOC201, DOC501

from __future__ import annotations

from datetime import UTC, datetime, time, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.kernel.serialization import canonical_digest

_LAST_HOUR = 23
_LAST_MINUTE = 59


def schedule_rollover(
    after: datetime, server_timezone: str, hour: int = 0, minute: int = 0
) -> datetime:
    """Return the next server-local rollover as aware UTC."""
    if after.tzinfo is None or after.utcoffset() != timedelta(0):
        raise ValueError("rollover scheduling requires aware UTC")
    try:
        zone = ZoneInfo(server_timezone)
    except ZoneInfoNotFoundError as error:
        raise ValueError("server timezone is unavailable") from error
    if not 0 <= hour <= _LAST_HOUR or not 0 <= minute <= _LAST_MINUTE:
        raise ValueError("server rollover clock is invalid")
    local_after = after.astimezone(zone)
    candidate = datetime.combine(local_after.date(), time(hour, minute), zone)
    if candidate <= local_after:
        candidate += timedelta(days=1)
    return candidate.astimezone(UTC)


def calculate_swap_rollover(  # noqa: C901, PLR0912 - explicit fail-closed matrix.
    *,
    rollover_at: datetime,
    server_timezone: str,
    side: str,
    volume: Decimal,
    rate: Decimal,
    weekday_ratios: dict[int, Decimal],
    unit: str,
    point_value: Decimal | None,
    fx_rate: Decimal | None,
    posting_mode: str,
    posting_evidence_reference: str | None = None,
    position_id: str,
) -> dict[str, object]:
    """Calculate signed swap accrual and gated provider posting semantics."""
    if rollover_at.tzinfo is None or rollover_at.utcoffset() != timedelta(0):
        raise ValueError("rollover timestamp must be aware UTC")
    try:
        local = rollover_at.astimezone(ZoneInfo(server_timezone))
    except ZoneInfoNotFoundError as error:
        raise ValueError("server timezone is unavailable") from error
    if side not in {"LONG", "SHORT"} or not volume.is_finite() or volume <= 0:
        raise ValueError("swap position input is invalid")
    if not rate.is_finite() or set(weekday_ratios) != set(range(7)):
        raise ValueError("complete finite weekday ratios are required")
    multiplier = weekday_ratios[local.weekday()]
    if not multiplier.is_finite() or multiplier < 0:
        raise ValueError("weekday ratio is invalid")
    if unit == "POINTS":
        if point_value is None or not point_value.is_finite():
            raise ValueError("POINTS swap requires point-value evidence")
        amount = rate * volume * multiplier * point_value
    elif unit == "ACCOUNT_CURRENCY":
        amount = rate * volume * multiplier
    elif unit == "PROFIT_CURRENCY":
        if fx_rate is None or not fx_rate.is_finite() or fx_rate <= 0:
            raise ValueError("profit-currency swap requires FX evidence")
        amount = rate * volume * multiplier * fx_rate
    else:
        raise ValueError("swap calculation unit is unsupported")
    if posting_mode not in {"ACCRUAL_ONLY", "BALANCE_POSTING", "REOPEN"}:
        raise ValueError("swap posting mode is unsupported")
    if posting_mode != "ACCRUAL_ONLY" and not posting_evidence_reference:
        raise ValueError("provider posting mode requires target evidence")
    result: dict[str, object] = {
        "rollover_at": rollover_at.isoformat(),
        "weekday": local.weekday(),
        "multiplier": str(multiplier),
        "accrued_amount": str(amount),
        "balance_posted": posting_mode == "BALANCE_POSTING",
        "posting_mode": posting_mode,
    }
    if posting_mode == "REOPEN":
        identity = canonical_digest(
            {"position_id": position_id, "rollover_at": rollover_at, "amount": amount}
        )
        result.update(
            closed_position_id=position_id,
            reopened_position_id=f"reopen-{identity}",
            close_deal_id=f"deal-close-{identity}",
            open_deal_id=f"deal-open-{identity}",
        )
    return result


__all__ = ["calculate_swap_rollover", "schedule_rollover"]
