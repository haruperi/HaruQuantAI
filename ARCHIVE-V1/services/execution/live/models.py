"""Live Trading Domain Models.

Classes and functions:
    SignalType: Class. Provides SignalType behavior for execution workflows.
    Signal: Class. Provides Signal behavior for execution workflows.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel


class SignalType(str, Enum):
    """Signal types."""

    BUY = "buy"
    SELL = "sell"
    CLOSE = "close"
    CLOSE_BUY = "close buy"
    CLOSE_SELL = "close sell"


class Signal(BaseModel):
    """Standardized Trading Signal."""

    symbol: str
    timeframe: str
    signal_type: str  # buy, sell, etc.
    signal_time: str
    entry_price: float | None = None
    stop_loss: float | None = None
    take_profit: float | None = None
    reason: str | None = None
    metadata: dict[str, Any] | None = None

    # Risk management fields
    risk_pips: float | None = None
    risk_usd: float | None = None
    position_size: float | None = None
    reward_risk_ratio: float | None = None

    class Config:
        """Pydantic config."""

        use_enum_values = True
