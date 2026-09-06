# ruff: noqa: N801, N816, RUF022, RUF100  # Exact public names/order.
"""Generated MQL5-based contract vocabulary. DO NOT EDIT."""

from __future__ import annotations

from enum import IntEnum
from typing import Final


class ENUM_TIMEFRAMES(IntEnum):
    """Defines the identifier set for timeframes."""

    PERIOD_CURRENT = 0
    PERIOD_M1 = 1
    PERIOD_M2 = 2
    PERIOD_M3 = 3
    PERIOD_M4 = 4
    PERIOD_M5 = 5
    PERIOD_M6 = 6
    PERIOD_M10 = 10
    PERIOD_M12 = 12
    PERIOD_M15 = 15
    PERIOD_M20 = 20
    PERIOD_M30 = 30
    PERIOD_H1 = 16385
    PERIOD_H2 = 16386
    PERIOD_H3 = 16387
    PERIOD_H4 = 16388
    PERIOD_H6 = 16390
    PERIOD_H8 = 16392
    PERIOD_H12 = 16396
    PERIOD_D1 = 16408
    PERIOD_W1 = 32769
    PERIOD_MN1 = 49153


PERIOD_CURRENT: Final = ENUM_TIMEFRAMES.PERIOD_CURRENT
PERIOD_M1: Final = ENUM_TIMEFRAMES.PERIOD_M1
PERIOD_M2: Final = ENUM_TIMEFRAMES.PERIOD_M2
PERIOD_M3: Final = ENUM_TIMEFRAMES.PERIOD_M3
PERIOD_M4: Final = ENUM_TIMEFRAMES.PERIOD_M4
PERIOD_M5: Final = ENUM_TIMEFRAMES.PERIOD_M5
PERIOD_M6: Final = ENUM_TIMEFRAMES.PERIOD_M6
PERIOD_M10: Final = ENUM_TIMEFRAMES.PERIOD_M10
PERIOD_M12: Final = ENUM_TIMEFRAMES.PERIOD_M12
PERIOD_M15: Final = ENUM_TIMEFRAMES.PERIOD_M15
PERIOD_M20: Final = ENUM_TIMEFRAMES.PERIOD_M20
PERIOD_M30: Final = ENUM_TIMEFRAMES.PERIOD_M30
PERIOD_H1: Final = ENUM_TIMEFRAMES.PERIOD_H1
PERIOD_H2: Final = ENUM_TIMEFRAMES.PERIOD_H2
PERIOD_H3: Final = ENUM_TIMEFRAMES.PERIOD_H3
PERIOD_H4: Final = ENUM_TIMEFRAMES.PERIOD_H4
PERIOD_H6: Final = ENUM_TIMEFRAMES.PERIOD_H6
PERIOD_H8: Final = ENUM_TIMEFRAMES.PERIOD_H8
PERIOD_H12: Final = ENUM_TIMEFRAMES.PERIOD_H12
PERIOD_D1: Final = ENUM_TIMEFRAMES.PERIOD_D1
PERIOD_W1: Final = ENUM_TIMEFRAMES.PERIOD_W1
PERIOD_MN1: Final = ENUM_TIMEFRAMES.PERIOD_MN1

_TIMEFRAME_CODES: Final[dict[ENUM_TIMEFRAMES, str]] = {
    PERIOD_CURRENT: "CURRENT",
    PERIOD_M1: "M1",
    PERIOD_M2: "M2",
    PERIOD_M3: "M3",
    PERIOD_M4: "M4",
    PERIOD_M5: "M5",
    PERIOD_M6: "M6",
    PERIOD_M10: "M10",
    PERIOD_M12: "M12",
    PERIOD_M15: "M15",
    PERIOD_M20: "M20",
    PERIOD_M30: "M30",
    PERIOD_H1: "H1",
    PERIOD_H2: "H2",
    PERIOD_H3: "H3",
    PERIOD_H4: "H4",
    PERIOD_H6: "H6",
    PERIOD_H8: "H8",
    PERIOD_H12: "H12",
    PERIOD_D1: "D1",
    PERIOD_W1: "W1",
    PERIOD_MN1: "MN1",
}


def timeframe_code(value: ENUM_TIMEFRAMES) -> str:
    """Return the stable HaruQuantAI boundary code."""
    return _TIMEFRAME_CODES[value]


def parse_timeframe(value: object) -> ENUM_TIMEFRAMES:
    """Parse an integer or boundary code into a standard period.

    Returns:
        The canonical standard timeframe.

    Raises:
        ValueError: If the value is not a supported standard timeframe.
    """
    if isinstance(value, bool):
        message = f"unsupported standard timeframe: {value!r}"
        raise ValueError(message)  # noqa: TRY004  # bool is not a period
    if isinstance(value, ENUM_TIMEFRAMES):
        return value
    if isinstance(value, int):
        return ENUM_TIMEFRAMES(value)
    if isinstance(value, str):
        cleaned = value.strip().upper()
        direct = ENUM_TIMEFRAMES.__members__.get(f"PERIOD_{cleaned}")
        if direct is not None:
            return direct
        for period, code in _TIMEFRAME_CODES.items():
            if cleaned == code or cleaned == _reverse_code(code):
                return period
    message = f"unsupported standard timeframe: {value!r}"
    raise ValueError(message)


def _reverse_code(code: str) -> str:
    if code.startswith("MN"):
        return f"{code[2:]}MN"
    return f"{code[1:]}{code[0]}" if len(code) > 1 else code


__all__ = [
    "ENUM_TIMEFRAMES",
    "parse_timeframe",
    "PERIOD_CURRENT",
    "PERIOD_D1",
    "PERIOD_H1",
    "PERIOD_H2",
    "PERIOD_H3",
    "PERIOD_H4",
    "PERIOD_H6",
    "PERIOD_H8",
    "PERIOD_H12",
    "PERIOD_M1",
    "PERIOD_M2",
    "PERIOD_M3",
    "PERIOD_M4",
    "PERIOD_M5",
    "PERIOD_M6",
    "PERIOD_M10",
    "PERIOD_M12",
    "PERIOD_M15",
    "PERIOD_M20",
    "PERIOD_M30",
    "PERIOD_MN1",
    "PERIOD_W1",
    "timeframe_code",
]
