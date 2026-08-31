"""Deterministic consumer test fixture requiring indicator.rsi.v1 capability."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

from app.contracts.indicator.rsi.v1 import RsiCapabilityV1
from app.kernel.identifiers import CapabilityId

if TYPE_CHECKING:
    from app.kernel.effects import EffectScope

_RSI_CAPABILITY_ID = CapabilityId.parse("indicator.rsi.v1")

__all__: tuple[str, ...] = ("RsiConsumerCapabilityV1", "create_provider")


@dataclass(frozen=True, slots=True)
class RsiConsumerCapabilityV1:
    """Capability exposed by the test RSI consumer."""

    rsi_cap: RsiCapabilityV1


def create_provider(
    *,
    dependencies: Mapping[CapabilityId, object],
    config: Mapping[str, object],
    scope: EffectScope,
) -> RsiConsumerCapabilityV1:
    """Factory creating RsiConsumerCapabilityV1 with injected RSI capability."""
    _ = (config, scope)
    rsi_inst = dependencies.get(_RSI_CAPABILITY_ID)
    if not isinstance(rsi_inst, RsiCapabilityV1):
        raise TypeError(f"Expected RsiCapabilityV1, got {type(rsi_inst)}")
    return RsiConsumerCapabilityV1(rsi_cap=cast("RsiCapabilityV1", rsi_inst))
