"""Single-bar, Quote, Multi-timeframe, Session, and Heiken Ashi price blocks.

Description:
    Exports StrategyQuant-faithful price building blocks, class aliases,
    data containers, calculators, and the unified Price facade.
Purpose:
    FEAT-PRICE-BLOCKS: StrategyQuant donor-faithful price blocks.
Key Capabilities:
    - FR-PRICE-EXPORTS: Package-level exports for all price blocks and facades.
Python API Usage:
    from app.extend.blocks.price import (
        Close,
        High,
        Low,
        Open,
        Price,
        Prices,
    )
CLI Usage:
    uv run pytest tests/extend/blocks/test_price.py --no-cov
"""

from __future__ import annotations

from app.extend.blocks.price._common import (
    DEFAULT_PIP_SIZE,
    HOURS_IN_DAY,
    MINUTES_IN_HOUR,
    SECONDS_IN_HOUR,
    SECONDS_IN_MINUTE,
    BarPrice,
    MTFPrice,
    QuotePrice,
    SessionPrice,
    _normalize_timestamps,
)
from app.extend.blocks.price.ask import Ask, ask, ask_spec
from app.extend.blocks.price.bid import Bid, bid, bid_spec
from app.extend.blocks.price.close import (
    Close,
    bar_close,
    close_price,
    close_spec,
)
from app.extend.blocks.price.close_d import CloseD, close_d, close_d_spec
from app.extend.blocks.price.close_m import CloseM, close_m, close_m_spec
from app.extend.blocks.price.close_w import CloseW, close_w, close_w_spec
from app.extend.blocks.price.facade import Price, Prices
from app.extend.blocks.price.heiken_ashi_close import (
    HeikenAshiClose,
    heiken_ashi_close,
    heiken_ashi_close_spec,
)
from app.extend.blocks.price.heiken_ashi_high import (
    HeikenAshiHigh,
    heiken_ashi_high,
    heiken_ashi_high_spec,
)
from app.extend.blocks.price.heiken_ashi_low import (
    HeikenAshiLow,
    heiken_ashi_low,
    heiken_ashi_low_spec,
)
from app.extend.blocks.price.heiken_ashi_open import (
    HeikenAshiOpen,
    heiken_ashi_open,
    heiken_ashi_open_spec,
)
from app.extend.blocks.price.high import High, bar_high, high_price, high_spec
from app.extend.blocks.price.high_d import HighD, high_d, high_d_spec
from app.extend.blocks.price.high_m import HighM, high_m, high_m_spec
from app.extend.blocks.price.high_w import HighW, high_w, high_w_spec
from app.extend.blocks.price.low import Low, bar_low, low_price, low_spec
from app.extend.blocks.price.low_d import LowD, low_d, low_d_spec
from app.extend.blocks.price.low_m import LowM, low_m, low_m_spec
from app.extend.blocks.price.low_w import LowW, low_w, low_w_spec
from app.extend.blocks.price.open import Open, bar_open, open_price, open_spec
from app.extend.blocks.price.open_d import OpenD, open_d, open_d_spec
from app.extend.blocks.price.open_m import OpenM, open_m, open_m_spec
from app.extend.blocks.price.open_w import OpenW, open_w, open_w_spec
from app.extend.blocks.price.session_close import (
    SessionClose,
    session_close,
    session_close_spec,
)
from app.extend.blocks.price.session_high import (
    SessionHigh,
    session_high,
    session_high_spec,
)
from app.extend.blocks.price.session_low import (
    SessionLow,
    session_low,
    session_low_spec,
)
from app.extend.blocks.price.session_ohlc_calculator import (
    CLOSE,
    HIGH,
    LOW,
    OPEN,
    SessionOHLCCalculator,
)
from app.extend.blocks.price.session_open import (
    SessionOpen,
    session_open,
    session_open_spec,
)
from app.extend.blocks.price.spread import Spread, spread, spread_spec
from app.extend.blocks.price.spread_in_pips import (
    SpreadInPips,
    spread_in_pips,
    spread_in_pips_spec,
)
from app.extend.blocks.price.volume import (
    Volume,
    bar_volume,
    volume_price,
    volume_spec,
)

__all__ = [
    "CLOSE",
    "DEFAULT_PIP_SIZE",
    "HIGH",
    "HOURS_IN_DAY",
    "LOW",
    "MINUTES_IN_HOUR",
    "OPEN",
    "SECONDS_IN_HOUR",
    "SECONDS_IN_MINUTE",
    "Ask",
    "BarPrice",
    "Bid",
    "Close",
    "CloseD",
    "CloseM",
    "CloseW",
    "HeikenAshiClose",
    "HeikenAshiHigh",
    "HeikenAshiLow",
    "HeikenAshiOpen",
    "High",
    "HighD",
    "HighM",
    "HighW",
    "Low",
    "LowD",
    "LowM",
    "LowW",
    "MTFPrice",
    "Open",
    "OpenD",
    "OpenM",
    "OpenW",
    "Price",
    "Prices",
    "QuotePrice",
    "SessionClose",
    "SessionHigh",
    "SessionLow",
    "SessionOHLCCalculator",
    "SessionOpen",
    "SessionPrice",
    "Spread",
    "SpreadInPips",
    "Volume",
    "_normalize_timestamps",
    "ask",
    "ask_spec",
    "bar_close",
    "bar_high",
    "bar_low",
    "bar_open",
    "bar_volume",
    "bid",
    "bid_spec",
    "close_d",
    "close_d_spec",
    "close_m",
    "close_m_spec",
    "close_price",
    "close_spec",
    "close_w",
    "close_w_spec",
    "heiken_ashi_close",
    "heiken_ashi_close_spec",
    "heiken_ashi_high",
    "heiken_ashi_high_spec",
    "heiken_ashi_low",
    "heiken_ashi_low_spec",
    "heiken_ashi_open",
    "heiken_ashi_open_spec",
    "high_d",
    "high_d_spec",
    "high_m",
    "high_m_spec",
    "high_price",
    "high_spec",
    "high_w",
    "high_w_spec",
    "low_d",
    "low_d_spec",
    "low_m",
    "low_m_spec",
    "low_price",
    "low_spec",
    "low_w",
    "low_w_spec",
    "open_d",
    "open_d_spec",
    "open_m",
    "open_m_spec",
    "open_price",
    "open_spec",
    "open_w",
    "open_w_spec",
    "session_close",
    "session_close_spec",
    "session_high",
    "session_high_spec",
    "session_low",
    "session_low_spec",
    "session_open",
    "session_open_spec",
    "spread",
    "spread_in_pips",
    "spread_in_pips_spec",
    "spread_spec",
    "volume_price",
    "volume_spec",
]
