"""Post-backtest WhatIf transformations; independent of strategy block discovery."""

from .base import BaseWhatIf, WhatIfRecord
from .by_days import ByDays
from .by_hours import ByHours
from .by_months import ByMonths
from .exclude_overlapping_trades import ExcludeOverlappingTrades
from .exclude_pct_trades_with_biggest_pl import ExcludePctTradesWithBiggestPl
from .exclude_pct_trades_with_lowest_pl import ExcludePctTradesWithLowestPl
from .exclude_short_trades import ExcludeShortTrades
from .exclude_trades_with_biggest_pl import ExcludeTradesWithBiggestPl
from .exclude_trades_with_lowest_pl import ExcludeTradesWithLowestPl
from .remove_balance_transactions import RemoveBalanceTransactions
from .remove_pending_trades import RemovePendingTrades
from .swap import Swap
from .take_every_second_trade import TakeEverySecondTrade
from .take_max_trades_per_day import TakeMaxTradesPerDay
from .use_fixed_lots import UseFixedLots

SCENARIOS: tuple[type[BaseWhatIf], ...] = (
    ByDays,
    ByHours,
    ByMonths,
    ExcludeOverlappingTrades,
    ExcludePctTradesWithBiggestPl,
    ExcludePctTradesWithLowestPl,
    ExcludeShortTrades,
    ExcludeTradesWithBiggestPl,
    ExcludeTradesWithLowestPl,
    RemoveBalanceTransactions,
    RemovePendingTrades,
    Swap,
    TakeEverySecondTrade,
    TakeMaxTradesPerDay,
    UseFixedLots,
)

__all__ = [
    "SCENARIOS",
    "BaseWhatIf",
    "ByDays",
    "ByHours",
    "ByMonths",
    "ExcludeOverlappingTrades",
    "ExcludePctTradesWithBiggestPl",
    "ExcludePctTradesWithLowestPl",
    "ExcludeShortTrades",
    "ExcludeTradesWithBiggestPl",
    "ExcludeTradesWithLowestPl",
    "RemoveBalanceTransactions",
    "RemovePendingTrades",
    "Swap",
    "TakeEverySecondTrade",
    "TakeMaxTradesPerDay",
    "UseFixedLots",
    "WhatIfRecord",
]
