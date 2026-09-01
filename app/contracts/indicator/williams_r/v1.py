"""Williams %R capability v1 contract."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

CAPABILITY_ID = "indicator.williams_r.v1"

type WilliamsRFunctionV1 = Callable[..., Any]


@dataclass(frozen=True, slots=True)
class WilliamsRCapabilityV1:
    """Williams %R capability provider wrapper."""

    calculate: WilliamsRFunctionV1


__all__ = (
    "CAPABILITY_ID",
    "WilliamsRCapabilityV1",
    "WilliamsRFunctionV1",
)
