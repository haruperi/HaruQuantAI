"""Bitfinex public REST market data adapter for cryptocurrency historical candles.

Description:
    Implements a bounded, read-only historical candlestick adapter for Bitfinex
    using the official v2 public REST candles API. Conforms to the `data.provider`
    contract with explicit rate limits, cooperative cancellation, and normalized
    bar representations. Disallows order execution and account mutations.

Purpose:
    FEAT-BROKER-CRYPTO-BITFINEX: Bitfinex exchange historical market data adapter.

Key Capabilities:
    - FR-BROKER-BITFINEX-CANDLES: Fetch and normalize historical candles from Bitfinex API v2.
      Associated: `BitfinexExchangeAdapter.fetch_bars()`
      Logging: Emits DEBUG when requesting candles and logging received record counts.

Python API Usage:
    ```python
    from app.services.brokers.exchanges.bitfinex import BitfinexExchangeAdapter

    adapter = BitfinexExchangeAdapter()
    bars = adapter.fetch_bars(symbol="tBTCUSD", timeframe="1h", count=50)
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/services/brokers/test_brokers_rest_and_cdn_providers.py --no-cov
    ```
"""

from __future__ import annotations

from typing import Any

import requests
from app.host.logging import get_logger
from app.services.brokers._http import create_http_session, execute_bounded_get
from app.services.brokers.capabilities import CancellationToken

logger = get_logger(__name__)

CANDLES_FR = "FR-BROKER-BITFINEX-CANDLES"

__all__ = ["BitfinexExchangeAdapter"]

TIMEFRAME_MAP: dict[str, str] = {
    "M1": "1m",
    "1M": "1m",
    "1m": "1m",
    "M5": "5m",
    "5M": "5m",
    "5m": "5m",
    "M15": "15m",
    "15M": "15m",
    "15m": "15m",
    "M30": "30m",
    "30M": "30m",
    "30m": "30m",
    "H1": "1h",
    "1H": "1h",
    "1h": "1h",
    "H3": "3h",
    "3H": "3h",
    "H6": "6h",
    "6H": "6h",
    "H12": "12h",
    "12H": "12h",
    "D1": "1D",
    "1D": "1D",
    "1d": "1D",
    "W1": "1W",
    "1W": "1W",
    "MN1": "1M",
    "1MN": "1M",
}


class BitfinexExchangeAdapter:
    """Read-only market data adapter for Bitfinex exchange."""

    BASE_URL = "https://api-pub.bitfinex.com"

    def __init__(self, session: requests.Session | None = None) -> None:
        self.session = session or create_http_session("HaruQuantAI-BitfinexAdapter/1.0")

    def fetch_bars(
        self,
        *,
        symbol: str,
        timeframe: str,
        start: int = 0,
        end: int = 0,
        count: int = 100,
        limit: int = 1000,
        token: CancellationToken | None = None,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """Fetch historical candlestick bars from Bitfinex v2 candles endpoint."""
        sym = symbol.strip().upper()
        if not sym.startswith("T"):
            sym = f"t{sym}"

        tf = TIMEFRAME_MAP.get(
            timeframe.strip().upper(), TIMEFRAME_MAP.get(timeframe.strip(), "1m")
        )
        url = f"{self.BASE_URL}/v2/candles/trade:{tf}:{sym}/hist"

        target_limit = min(max(count, limit), 1000)
        params: dict[str, Any] = {"limit": target_limit, "sort": 1}
        if start and start > 0:
            params["start"] = start * 1000 if start < 100_000_000_000 else start
        if end and end > 0:
            params["end"] = end * 1000 if end < 100_000_000_000 else end

        resp = execute_bounded_get(
            self.session,
            url,
            params=params,
            token=token,
            provider="crypto:bitfinex",
        )
        if resp.status_code != 200:
            logger.warning(
                "%s: Bitfinex returned status %d for %s",
                CANDLES_FR,
                resp.status_code,
                sym,
            )
            return []

        payload = resp.json()
        if not isinstance(payload, list):
            return []

        rows: list[dict[str, Any]] = []
        for item in payload:
            if not isinstance(item, list) or len(item) < 6:
                continue
            # Layout: [MTS, OPEN, CLOSE, HIGH, LOW, VOLUME]
            mts, o, c, h, l, v = item[0], item[1], item[2], item[3], item[4], item[5]
            rows.append(
                {
                    "time": int(mts // 1000),
                    "open": float(o),
                    "high": float(h),
                    "low": float(l),
                    "close": float(c),
                    "tick_volume": int(v) if v else 1,
                    "spread": 0,
                    "real_volume": int(v) if v else 1,
                }
            )

        rows.sort(key=lambda r: r["time"])
        logger.debug("%s: Retrieved %d bars for %s", CANDLES_FR, len(rows), sym)
        return rows
