"""RSI capability v1 contract."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

CAPABILITY_ID = "indicator.rsi.v1"

type RsiFunctionV1 = Callable[..., Any]


@dataclass(frozen=True, slots=True)
class RsiCapabilityV1:
    """RSI capability provider wrapper."""

    calculate: RsiFunctionV1


__all__ = (
    "CAPABILITY_ID",
    "RsiCapabilityV1",
    "RsiFunctionV1",
)
