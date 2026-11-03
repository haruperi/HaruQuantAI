"""Monte Carlo Retest Perturbation Catalog.

Description:
    Provides MCRetestPerturbator implementing all 9 Monte Carlo Retest
    perturbations on price bars, spreads, slippage, starting bars, and
    strategy parameters.

Purpose:
    FEAT-RETESTER-MC-RETEST: Perturbations for robust backtest evaluation.

Key Capabilities:
    - FR-mc-retest-history: Perturb OHLC history data and fixed ranges.
    - FR-mc-retest-spread-slippage: Randomize spreads and execution slippage.
    - FR-mc-retest-parameters: Perturb parameters with configurable ranges.

Python API Usage:
    from app.extend.monte_carlo.retest.catalog import MCRetestPerturbator
    strat, bars = MCRetestPerturbator.perturb(
        "RandomizeSpread", strat, bars, {"min_spread": 1, "max_spread": 3}
    )

CLI Usage:
    python -m app.cli retest mc-perturb --method RandomizeSpread --seed 42
"""

from __future__ import annotations

import random
from collections.abc import Mapping, Sequence
from dataclasses import replace
from typing import Any

from app.core.data.contracts import MarketBar
from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError
from app.core.trading.strategy.hsl.models import HSLStrategyDocument
from app.extend.monte_carlo.retest.base import MonteCarloRetest
from app.extend.monte_carlo.retest.randomize_history_data import (
    RandomizeHistoryData,
)
from app.extend.monte_carlo.retest.randomize_history_data_fixed_range import (
    RandomizeHistoryDataFixedRange,
)
from app.extend.monte_carlo.retest.randomize_history_data_ohlc import (
    RandomizeHistoryDataOHLC,
)
from app.extend.monte_carlo.retest.randomize_min_distance import (
    RandomizeMinDistance,
)
from app.extend.monte_carlo.retest.randomize_slippage import RandomizeSlippage
from app.extend.monte_carlo.retest.randomize_spread import RandomizeSpread
from app.extend.monte_carlo.retest.randomize_starting_bar import (
    RandomizeStartingBar,
)
from app.extend.monte_carlo.retest.randomize_strategy_parameters import (
    RandomizeStrategyParameters,
)
from app.extend.monte_carlo.retest.randomize_strategy_parameters_customizable import (
    RandomizeStrategyParametersCustomizable,
)

logger = get_logger(__name__)

BarRecord = MarketBar

# Map of all 9 donor snippet classes
RETEST_CLASSES: dict[str, type[MonteCarloRetest]] = {
    "RandomizeHistoryData": RandomizeHistoryData,
    "RandomizeHistoryDataFixedRange": RandomizeHistoryDataFixedRange,
    "RandomizeHistoryDataOHLC": RandomizeHistoryDataOHLC,
    "RandomizeMinDistance": RandomizeMinDistance,
    "RandomizeSlippage": RandomizeSlippage,
    "RandomizeSpread": RandomizeSpread,
    "RandomizeStartingBar": RandomizeStartingBar,
    "RandomizeStrategyParameters": RandomizeStrategyParameters,
    "RandomizeStrategyParametersCustomizable": (
        RandomizeStrategyParametersCustomizable
    ),
}


class MCRetestPerturbator:
    """Catalog and applicator for all 9 Monte Carlo Retest perturbation methods."""

    METHODS: tuple[str, ...] = tuple(RETEST_CLASSES.keys())

    @classmethod
    def get_retest_class(cls, definition_id: str) -> type[MonteCarloRetest]:
        """Look up the perturbation class for a definition ID."""
        if definition_id not in RETEST_CLASSES:
            raise DomainError(
                code="RETEST_METHOD_NOT_FOUND",
                message=f"Monte Carlo retest method '{definition_id}' not found",
                details={"definition_id": definition_id},
            )
        return RETEST_CLASSES[definition_id]

    @classmethod
    def create_retest(cls, definition_id: str, **kwargs: Any) -> MonteCarloRetest:
        """Instantiate a Monte Carlo retest perturbation class."""
        retest_cls = cls.get_retest_class(definition_id)
        return retest_cls(**kwargs)

    @classmethod
    def perturb(
        cls,
        definition_id: str,
        strategy: HSLStrategyDocument,
        bars: Sequence[MarketBar],
        params: Mapping[str, Any] | None = None,
        *,
        seed: int = 42,
    ) -> tuple[HSLStrategyDocument, tuple[MarketBar, ...]]:
        """Apply the specified Monte Carlo retest perturbation.

        Args:
            definition_id: Method identifier (one of METHODS).
            strategy: HSLStrategyDocument candidate.
            bars: Input sequence of MarketBar records.
            params: Optional method-specific parameters.
            seed: Deterministic integer seed.

        Returns:
            Tuple of (perturbed HSLStrategyDocument, perturbed MarketBar tuple).
        """
        p = params or {}
        rng = random.Random(seed)  # noqa: S311

        if definition_id in (
            "RandomizeHistoryData",
            "RandomizeHistoryDataFixedRange",
            "RandomizeHistoryDataOHLC",
            "RandomizeMinDistance",
            "RandomizeSpread",
            "RandomizeStartingBar",
        ):
            new_bars = cls._perturb_bars(definition_id, bars, p, rng)
            return strategy, new_bars

        if definition_id == "RandomizeSlippage":
            return cls._perturb_slippage(strategy, bars, p, rng)

        if definition_id in (
            "RandomizeStrategyParameters",
            "RandomizeStrategyParametersCustomizable",
        ):
            new_strat = cls._perturb_params(definition_id, strategy, p, rng)
            return new_strat, tuple(bars)

        return strategy, tuple(bars)

    @classmethod
    def _perturb_bars(
        cls,
        definition_id: str,
        bars: Sequence[MarketBar],
        p: Mapping[str, Any],
        rng: random.Random,
    ) -> tuple[MarketBar, ...]:
        """Apply price bar perturbations."""
        if definition_id == "RandomizeHistoryData":
            pct = float(p.get("pct", 0.2)) / 100.0
            perturbed = [
                replace(
                    b,
                    open=round(b.open + (rng.uniform(-1.0, 1.0) * pct) * b.close, 5),
                    high=round(b.high + (rng.uniform(-1.0, 1.0) * pct) * b.close, 5),
                    low=round(b.low + (rng.uniform(-1.0, 1.0) * pct) * b.close, 5),
                    close=round(b.close + (rng.uniform(-1.0, 1.0) * pct) * b.close, 5),
                )
                for b in bars
            ]
            logger.info(
                "FR-mc-retest-history: perturbed %d bars (pct=%.2f)",
                len(bars),
                pct * 100,
            )
            return tuple(perturbed)

        if definition_id == "RandomizeHistoryDataFixedRange":
            pips = float(p.get("range_pips", 2.0)) * 0.0001
            return tuple(
                replace(
                    b,
                    open=round(b.open + rng.uniform(-pips, pips), 5),
                    high=round(b.high + rng.uniform(-pips, pips), 5),
                    low=round(b.low + rng.uniform(-pips, pips), 5),
                    close=round(b.close + rng.uniform(-pips, pips), 5),
                )
                for b in bars
            )

        if definition_id == "RandomizeHistoryDataOHLC":
            pct = float(p.get("pct", 0.1)) / 100.0
            ohlc_bars = []
            for b in bars:
                o = b.open + rng.uniform(-pct, pct) * b.open
                c = b.close + rng.uniform(-pct, pct) * b.close
                h = max(o, c, b.high + rng.uniform(0.0, pct) * b.high)
                low_val = min(o, c, b.low - rng.uniform(0.0, pct) * b.low)
                ohlc_bars.append(
                    replace(
                        b,
                        open=round(o, 5),
                        high=round(h, 5),
                        low=round(low_val, 5),
                        close=round(c, 5),
                    )
                )
            return tuple(ohlc_bars)

        if definition_id == "RandomizeMinDistance":
            min_dist = max(1, int(p.get("min_distance", 1)))
            return tuple(bars[::min_dist])

        if definition_id == "RandomizeSpread":
            min_spread = int(p.get("min_spread", 1))
            max_spread = int(p.get("max_spread", 5))
            spread_bars = [
                replace(b, spread=rng.randint(min_spread, max_spread)) for b in bars
            ]
            logger.info(
                "FR-mc-retest-spread-slippage: perturbed spreads in [%d, %d]",
                min_spread,
                max_spread,
            )
            return tuple(spread_bars)

        # RandomizeStartingBar
        max_offset = min(int(p.get("max_offset", 50)), max(0, len(bars) - 10))
        offset = rng.randint(0, max_offset) if max_offset > 0 else 0
        logger.info("FR-mc-retest-history: offset starting bar by %d", offset)
        return tuple(bars[offset:])

    @classmethod
    def _perturb_slippage(
        cls,
        strategy: HSLStrategyDocument,
        bars: Sequence[MarketBar],
        p: Mapping[str, Any],
        rng: random.Random,
    ) -> tuple[HSLStrategyDocument, tuple[MarketBar, ...]]:
        """Apply slippage perturbation."""
        add_slip = float(p.get("additional_slippage", 1.0)) * rng.uniform(0.5, 1.5)
        new_params = dict(strategy.strategy.parameters)
        if "slippage_points" in new_params:
            orig = float(new_params["slippage_points"].default)
            new_params["slippage_points"] = new_params["slippage_points"].model_copy(
                update={"default": round(orig + add_slip, 2)}
            )
        updated_payload = strategy.strategy.model_copy(
            update={"parameters": new_params}
        )
        return strategy.model_copy(update={"strategy": updated_payload}), tuple(bars)

    @classmethod
    def _perturb_params(
        cls,
        definition_id: str,
        strategy: HSLStrategyDocument,
        p: Mapping[str, Any],
        rng: random.Random,
    ) -> HSLStrategyDocument:
        """Apply parameter perturbations."""
        pct_change = float(p.get("pct_change", 10.0)) / 100.0
        allowed_keys = (
            p.get("parameter_names")
            if definition_id == "RandomizeStrategyParametersCustomizable"
            else None
        )
        new_params = dict(strategy.strategy.parameters)
        for k, param_spec in list(new_params.items()):
            if allowed_keys is not None and k not in allowed_keys:
                continue
            v = param_spec.default
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                factor = 1.0 + rng.uniform(-pct_change, pct_change)
                new_val = v * factor
                final_val = (
                    round(new_val, 4) if isinstance(v, float) else round(new_val)
                )
                new_params[k] = param_spec.model_copy(update={"default": final_val})
        logger.info("FR-mc-retest-parameters: perturbed parameters (%s)", definition_id)
        updated_payload = strategy.strategy.model_copy(
            update={"parameters": new_params}
        )
        return strategy.model_copy(update={"strategy": updated_payload})
