"""Approved public liquidity-indicator API.

Only ``amihud_illiquidity`` (spec ``IND-LQ-05``) is registered here. Per the
session plan's explicit judgment rule (the same rule already applied in
``order_flow/__init__.py``), the current ``MarketDataset``/``OHLCVRecord``
contract (``core/contracts.py``) carries only bar OHLCV — there is no
bid/ask, L2 order-book, or per-trade field. The remaining six spec
indicators are therefore intentionally omitted:

- ``IND-LQ-01`` (quoted/relative spread) needs a fresh best bid/ask.
- ``IND-LQ-02`` (effective spread) needs trade price plus a contemporaneous
  pre-trade midpoint and aggressor sign.
- ``IND-LQ-03`` (executable depth within a bps band) needs fresh L2 levels.
- ``IND-LQ-04`` (order-book depth slope) needs fresh ordered L2 levels.
- ``IND-LQ-06`` (Kyle lambda) needs interval mid-price change paired with
  signed quantity/notional flow, which bar OHLCV cannot reconstruct.
- ``IND-LQ-07`` (depth-to-requested-order ratio) needs executable depth
  (``IND-LQ-03``, unavailable) plus a caller-supplied requested quantity.

Only ``IND-LQ-05`` (Amihud illiquidity) is calculable from bar OHLCV alone
(interval return and interval dollar/notional volume), so it is the sole
built-in this module registers until Data publishes a book/trade-event
contract.
"""

from app.services.indicators.liquidity.amihud_illiquidity import amihud_illiquidity

__all__ = ["amihud_illiquidity"]
