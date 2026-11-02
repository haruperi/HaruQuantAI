"""ATM (Advanced Trade Management) multi-bracket exit strategy models.

Description:
    Enables multi-target and multi-exit behavior: partitioning position volume
    into brackets with distinct profit targets, stop losses, break-even triggers,
    trailing stops, and time-based bar-count exits, matching StrategyQuant ATM
    snippet logic.
Purpose:
    FEAT-ORDER-BLOCKS: StrategyQuant donor-faithful order execution blocks.
Key Capabilities:
    - FR-ORDER-ATM: Partition trade volume across multi-bracket exits.
Python API Usage:
    from app.extend.blocks.order.atm import ATMBracket, ATMStrategy
    strategy = ATMStrategy(brackets=(ATMBracket(0.5, 20.0), ATMBracket(0.5, 40.0)))
    exits = strategy.build_bracket_exits(0.1, 1.1000, 1, 0.0001)
CLI Usage:
    uv run pytest tests/extend/blocks/test_order_blocks.py --no-cov
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from app.core.host.logging import get_logger
from app.extend.blocks.order.sizing import normalize_lots

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class ATMBracket:
    """One exit bracket in a multi-target ATM strategy.

    Attributes:
        volume_fraction: Proportion of trade volume in (0.0, 1.0].
        profit_target_pips: Optional profit target distance in pips.
        stop_loss_pips: Optional initial stop loss distance in pips.
        move_sl_to_be_trigger_pips: Optional profit distance to trigger BE.
        move_sl_to_be_offset_pips: Offset in pips added to entry when moving to BE.
        trailing_distance_pips: Optional trailing stop distance in pips.
        trailing_activation_pips: Profit distance required before trailing starts.
        exit_after_bars: Optional bar count after which to close this bracket.
    """

    volume_fraction: float
    profit_target_pips: float | None = None
    stop_loss_pips: float | None = None
    move_sl_to_be_trigger_pips: float | None = None
    move_sl_to_be_offset_pips: float = 0.0
    trailing_distance_pips: float | None = None
    trailing_activation_pips: float = 0.0
    exit_after_bars: int | None = None

    def __post_init__(self) -> None:
        """Validate bracket parameters."""
        if not math.isfinite(self.volume_fraction) or not (
            0 < self.volume_fraction <= 1.0
        ):
            raise ValueError("volume_fraction must be in (0.0, 1.0]")
        for val, name in (
            (self.profit_target_pips, "profit_target_pips"),
            (self.stop_loss_pips, "stop_loss_pips"),
            (self.move_sl_to_be_trigger_pips, "move_sl_to_be_trigger_pips"),
            (self.move_sl_to_be_offset_pips, "move_sl_to_be_offset_pips"),
            (self.trailing_distance_pips, "trailing_distance_pips"),
            (self.trailing_activation_pips, "trailing_activation_pips"),
        ):
            if val is not None and (not math.isfinite(val) or val < 0):
                raise ValueError(f"{name} must be finite and nonnegative")
        if self.exit_after_bars is not None and (
            type(self.exit_after_bars) is not int or self.exit_after_bars < 0
        ):
            raise ValueError("exit_after_bars must be a nonnegative integer")


@dataclass(frozen=True, slots=True)
class ATMStrategy:
    """Multi-bracket ATM strategy orchestration."""

    brackets: tuple[ATMBracket, ...]

    def __post_init__(self) -> None:
        """Validate bracket collection and total volume fraction."""
        if not self.brackets:
            raise ValueError("ATMStrategy must contain at least one ATMBracket")
        total_fraction = sum(b.volume_fraction for b in self.brackets)
        if not math.isclose(total_fraction, 1.0, rel_tol=1e-5, abs_tol=1e-5):
            raise ValueError(
                f"Bracket volume fractions must sum to 1.0 (got {total_fraction:.4f})"
            )

    def split_volume(
        self,
        total_volume: float,
        *,
        lot_step: float = 0.01,
        min_lot: float = 0.01,
    ) -> list[float]:
        """Split total volume across brackets aligned to broker lot steps."""
        if not math.isfinite(total_volume) or total_volume < min_lot:
            raise ValueError(f"total_volume must be >= min_lot ({min_lot})")

        total_norm = normalize_lots(total_volume, min_lot=min_lot, lot_step=lot_step)
        volumes = []

        for bracket in self.brackets[:-1]:
            raw_vol = float(
                Decimal(str(total_norm)) * Decimal(str(bracket.volume_fraction))
            )
            vol = normalize_lots(raw_vol, min_lot=min_lot, lot_step=lot_step)
            volumes.append(vol)

        # Allocate remainder to final bracket to ensure exact sum conservation
        allocated = sum(Decimal(str(v)) for v in volumes)
        remaining = float(Decimal(str(total_norm)) - allocated)
        if remaining < min_lot:
            if volumes:
                volumes[-1] = float(Decimal(str(volumes[-1])) + Decimal(str(remaining)))
                remaining = 0.0
            else:
                remaining = min_lot
        volumes.append(remaining)
        logger.debug(
            "FR-ORDER-ATM: Split volume %s across %d brackets -> %s",
            total_volume,
            len(self.brackets),
            volumes,
        )
        return volumes

    def build_bracket_exits(
        self,
        total_volume: float,
        entry_price: float,
        direction: int,
        pip_size: float,
        *,
        lot_step: float = 0.01,
        min_lot: float = 0.01,
    ) -> list[dict[str, Any]]:
        """Compute volumes, price levels, and policy distances for each bracket."""
        if direction not in (1, -1):
            raise ValueError("direction must be 1 (Long) or -1 (Short)")
        volumes = self.split_volume(total_volume, lot_step=lot_step, min_lot=min_lot)

        bracket_specs = []
        for vol, bracket in zip(volumes, self.brackets, strict=True):
            tp_price = None
            if bracket.profit_target_pips is not None:
                tp_price = entry_price + direction * (
                    bracket.profit_target_pips * pip_size
                )

            sl_price = None
            if bracket.stop_loss_pips is not None:
                sl_price = entry_price - direction * (bracket.stop_loss_pips * pip_size)

            be_activation = None
            if bracket.move_sl_to_be_trigger_pips is not None:
                be_activation = bracket.move_sl_to_be_trigger_pips * pip_size

            be_offset = bracket.move_sl_to_be_offset_pips * pip_size

            trailing_dist = None
            if bracket.trailing_distance_pips is not None:
                trailing_dist = bracket.trailing_distance_pips * pip_size

            trailing_act = bracket.trailing_activation_pips * pip_size

            spec = {
                "volume": vol,
                "profit_target": tp_price,
                "stop_loss": sl_price,
                "move_sl_to_be": (
                    {"activation": be_activation, "offset": be_offset}
                    if be_activation is not None
                    else None
                ),
                "trailing_stop": (
                    {"distance": trailing_dist, "activation": trailing_act}
                    if trailing_dist is not None
                    else None
                ),
                "exit_after_bars": bracket.exit_after_bars,
            }
            bracket_specs.append(spec)
        logger.debug(
            "FR-ORDER-ATM: Built %d bracket exit specs for entry=%s dir=%s",
            len(bracket_specs),
            entry_price,
            direction,
        )
        return bracket_specs


__all__ = ["ATMBracket", "ATMStrategy"]
