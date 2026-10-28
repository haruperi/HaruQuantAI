"""Python boilerplate generators for the editor template catalog."""

from __future__ import annotations

import re


def _to_snake_case(name: str) -> str:
    """Convert PascalCase or mixed string to snake_case."""
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower().strip("_")


def _to_pascal_case(name: str) -> str:
    """Convert snake_case or arbitrary string to PascalCase."""
    snake = _to_snake_case(name)
    return "".join(part.capitalize() for part in snake.split("_") if part)


def _gen_indicator(name: str) -> str:
    cls_name = _to_pascal_case(name) or "CustomIndicator"
    block_name = _to_snake_case(name) or "custom_indicator"
    return f'''"""Custom technical indicator: {cls_name}."""

from typing import ClassVar, override
from pydantic import Field
from app.include.blocks.indicators.base import BaseIndicator
from app.include.blocks.metadata import BlockSpec, InputPort, OutputPort
from app.include.blocks.series import BarData, IndicatorSeries
from app.include.calculators.average import sma_kernel


class {cls_name}(BaseIndicator):
    """Calculate a validated moving average over closing prices."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.custom.{block_name}",
        name="{cls_name}",
        category="custom",
        inputs=(InputPort("close"),),
        outputs=(OutputPort("value"),),
        required_market_inputs=("close",),
    )
    period: int = Field(default=14, ge=1)

    @override
    def required_history(self) -> int:
        return self.period

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        bars.require_inputs(self.spec.required_market_inputs)
        return {{"value": IndicatorSeries(sma_kernel(bars.close, self.period))}}
'''


def _gen_signal(name: str) -> str:
    cls_name = _to_pascal_case(name) or "CustomSignal"
    return f'''"""Custom Strategy Signal Condition: {cls_name}.

Evaluates entry or exit conditions across indicator and price series.
"""

from dataclasses import dataclass
from app.include.price import BarPrice
from app.include.blocks.series import IndicatorSeries


@dataclass
class {cls_name}:
    """Evaluates whether entry/exit criteria are met."""

    threshold: float = 0.0

    def evaluate(self, series: IndicatorSeries, bars: BarPrice, bar_idx: int) -> bool:
        """Return True when signal condition triggers on the given bar."""
        if bar_idx < 1 or bar_idx >= len(series.values):
            return False
        return float(series.get(bar_idx)) > self.threshold
'''


def _gen_order(name: str) -> str:
    cls_name = _to_pascal_case(name) or "CustomOrderAction"
    return f'''"""Custom Order Action: {cls_name}.

Custom logic for opening, modifying, or closing trading orders.
"""

from dataclasses import dataclass
from typing import Any, Mapping
from app.include.enums import OrderType


@dataclass
class {cls_name}:
    """Defines custom order parameters and execution rules."""

    order_type: OrderType = OrderType.BUY
    magic_number: int = 10001

    def execute_order(self, symbol: str, size: float, price: float, **kwargs: Any) -> dict[str, Any]:
        """Prepare and return order dispatch specification."""
        return {{
            "symbol": symbol,
            "order_type": self.order_type.name,
            "type_code": self.order_type.value,
            "size": size,
            "price": price,
            "magic": self.magic_number,
        }}
'''


def _gen_other_actions(name: str) -> str:
    cls_name = _to_pascal_case(name) or "CustomAction"
    return f'''"""Custom Side-Effect Action: {cls_name}.

Performs state updates, alerts, chart markings, or notifications.
"""

from dataclasses import dataclass
from typing import Any
from app.host.logging import get_logger

logger = get_logger(__name__)


@dataclass
class {cls_name}:
    """Performs side-effect actions on event triggers."""

    action_label: str = "{cls_name}"

    def trigger(self, context: dict[str, Any]) -> None:
        """Execute the configured action with current context."""
        logger.info(f"Triggered action {{self.action_label}} with context keys: {{list(context.keys())}}")
'''


def _gen_databank_column(name: str) -> str:
    cls_name = _to_pascal_case(name) or "CustomMetric"
    return f'''"""Custom Databank Metric Column: {cls_name}.

Computes a strategy performance metric displayed in Databanks.
"""

from dataclasses import dataclass
from typing import Any, Sequence
from app.include.metrics.base import BaseMetric


@dataclass
class {cls_name}(BaseMetric):
    """Computes custom scalar metric from strategy trades."""

    name: str = "{cls_name}"
    decimal_places: int = 2

    def compute(self, trades: Sequence[dict[str, Any]], initial_capital: float = 10000.0) -> float:
        """Compute metric value from executed trades."""
        if not trades:
            return 0.0
        profits = [t.get("profit", 0.0) for t in trades]
        net_profit = sum(profits)
        return round(net_profit / initial_capital, self.decimal_places)
'''


def _gen_trade_column(name: str) -> str:
    cls_name = _to_pascal_case(name) or "CustomTradeColumn"
    return f'''"""Custom Trade Column: {cls_name}.

Computes custom analytics for an individual executed trade.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class {cls_name}:
    """Computes a per-trade analytic column."""

    name: str = "{cls_name}"

    def compute_trade_value(self, trade: dict[str, Any]) -> Any:
        """Calculate specific value for one trade record."""
        pnl = trade.get("profit", 0.0)
        duration_bars = trade.get("bars_held", 0)
        return round(pnl / max(1, duration_bars), 2)
'''


def _gen_money_management(name: str) -> str:
    cls_name = _to_pascal_case(name) or "CustomPositionSizer"
    return f'''"""Custom Money Management & Position Sizing: {cls_name}.

Calculates trade order size (lots/contracts) based on risk parameters.
"""

from dataclasses import dataclass
from app.include.blocks.money_management.base import BasePositionSizer


@dataclass
class {cls_name}(BasePositionSizer):
    """Calculates trade volume from risk and stop loss distance."""

    risk_percent: float = 1.0
    min_lots: float = 0.01
    max_lots: float = 10.0

    def compute_size(self, account_equity: float, stop_loss_pips: float, pip_value: float = 10.0) -> float:
        """Compute recommended lot size."""
        if stop_loss_pips <= 0:
            return self.min_lots
        risk_amount = account_equity * (self.risk_percent / 100.0)
        calculated_lots = risk_amount / (stop_loss_pips * pip_value)
        return max(self.min_lots, min(self.max_lots, round(calculated_lots, 2)))
'''


def _gen_monte_carlo_manipulation(name: str) -> str:
    cls_name = _to_pascal_case(name) or "CustomMonteCarloManipulation"
    return f'''"""Custom Monte Carlo Trade Manipulation: {cls_name}.

Performs trade resampling, reordering, or slippage perturbation.
"""

import random
from dataclasses import dataclass
from typing import Any, Sequence


@dataclass
class {cls_name}:
    """Manipulates trade sequence to stress test equity curves."""

    skip_probability: float = 0.05

    def manipulate_trades(self, trades: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
        """Return a randomized permutation of trades."""
        survivors = [t for t in trades if random.random() > self.skip_probability]
        random.shuffle(survivors)
        return survivors
'''


def _gen_monte_carlo_retest(name: str) -> str:
    cls_name = _to_pascal_case(name) or "CustomMonteCarloRetest"
    return f'''"""Custom Monte Carlo Parameter Retest: {cls_name}.

Perturbs strategy parameters to verify optimization stability.
"""

import random
from dataclasses import dataclass
from typing import Any, Mapping


@dataclass
class {cls_name}:
    """Jiggles parameters by a percentage to test robustness."""

    jitter_percent: float = 10.0

    def perturb_parameters(self, params: Mapping[str, Any]) -> dict[str, Any]:
        """Return perturbed parameter dictionary."""
        perturbed: dict[str, Any] = {{}}
        for key, val in params.items():
            if isinstance(val, (int, float)):
                factor = 1.0 + random.uniform(-self.jitter_percent, self.jitter_percent) / 100.0
                perturbed[key] = round(val * factor, 4) if isinstance(val, float) else max(1, int(round(val * factor)))
            else:
                perturbed[key] = val
        return perturbed
'''


def _gen_what_if(name: str) -> str:
    cls_name = _to_pascal_case(name) or "CustomWhatIfScenario"
    return f'''"""Custom What-If Scenario Filter: {cls_name}.

Filters or modifies historical trades under hypothetical conditions.
"""

from dataclasses import dataclass
from typing import Any, Sequence


@dataclass
class {cls_name}:
    """Filters trades according to scenario rules."""

    max_loss_filter: float = -500.0

    def filter_trades(self, trades: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
        """Filter out trades that fail the what-if threshold."""
        return [t for t in trades if t.get("profit", 0.0) >= self.max_loss_filter]
'''


def _gen_custom_analysis(name: str) -> str:
    cls_name = _to_pascal_case(name) or "CustomAnalysisScript"
    return f'''"""Custom Analysis Script: {cls_name}.

Batch reporting and analytical evaluations over databank strategies.
"""

from typing import Any, Mapping, Sequence


class {cls_name}:
    """Analytical processor for strategies and databanks."""

    def run_analysis(self, strategies: Sequence[dict[str, Any]]) -> dict[str, Any]:
        """Perform analysis and return structured findings."""
        count = len(strategies)
        return {{
            "analyzed_count": count,
            "status": "completed",
            "summary": f"Analyzed {{count}} strategies.",
        }}
'''


def _gen_ai_tools(name: str) -> str:
    cls_name = _to_pascal_case(name) or "CustomAITool"
    tool_name = f"ext_{_to_snake_case(name)}"
    return f'''"""Custom AI Assistant Tool: {cls_name}.

Registered dynamically as an MCP tool callable by AI agents.
"""

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass
class {cls_name}:
    """Custom AI agent callable tool."""

    name: str = "{tool_name}"
    description: str = "Custom analysis tool for AI assistant."

    def get_input_schema(self) -> dict[str, Any]:
        """Return JSON schema for tool arguments."""
        return {{
            "type": "object",
            "properties": {{
                "target_symbol": {{"type": "string", "description": "Symbol to evaluate"}},
            }},
            "required": ["target_symbol"],
        }}

    def run(self, arguments: Mapping[str, Any]) -> dict[str, Any]:
        """Execute tool logic and return response."""
        sym = arguments.get("target_symbol", "UNKNOWN")
        return {{"result": f"Executed custom tool for {{sym}} successfully."}}
'''
