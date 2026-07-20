"""Copy-ready strategy orchestration class."""

from __future__ import annotations

import pandas as pd
from app.services.strategy import MarketContext
from app.services.strategy.base import BaseStrategy
from app.services.strategy.pybots._template import rules


class TemplateStrategy(BaseStrategy):
    """Safe skeleton that emits no trade intents until its rules are implemented."""

    def calculate_signals(
        self, df: pd.DataFrame, context: MarketContext
    ) -> pd.DataFrame:
        """Map the four pure rule functions into the canonical signal contract."""
        df["long_entry"] = int(rules.long_entry_signal(context, self.config))
        df["short_entry"] = int(rules.short_entry_signal(context, self.config))
        df["long_exit"] = int(rules.long_exit_signal(context, self.config))
        df["short_exit"] = int(rules.short_exit_signal(context, self.config))
        return df
