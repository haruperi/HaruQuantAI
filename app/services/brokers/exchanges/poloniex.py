"""Poloniex public REST market data adapter for cryptocurrency historical candles.

Description:
    Implements a bounded, read-only historical candlestick adapter for Poloniex
    using the official public REST markets candles API. Conforms to the `data.provider`
    contract with interval mapping, cooperative cancellation, and normalized bar representations.

Purpose:
    FEAT-BROKER-CRYPTO-POLONIEX: Poloniex exchange historical market data adapter.

Key Capabilities:
    - FR-BROKER-POLONIEX-CANDLES: Fetch and normalize historical candles from Poloniex API.
      Associated: `PoloniexExchangeAdapter.fetch_bars()`
      Logging: Emits DEBUG when requesting candles and logging received record counts.

Python API Usage:
    ```python
    from app.services.brokers.exchanges.poloniex import PoloniexExchangeAdapter

    adapter = PoloniexExchangeAdapter()
    bars = adapter.fetch_bars(symbol="BTC_USDT", timeframe="1h", count=50)
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

CANDLES_FR = "FR-BROKER-POLONIEX-CANDLES"

__all__ = ["PoloniexExchangeAdapter"]

INTERVAL_MAP: dict[str, str] = {
    "M1": "MINUTE_1",
    "1M": "MINUTE_1",
    "1m": "MINUTE_1",
    "M5": "MINUTE_5",
    "5M": "MINUTE_5",
    "5m": "MINUTE_5",
    "M15": "MINUTE_15",
    "15M": "MINUTE_15",
    "15m": "MINUTE_15",
    "M30": "MINUTE_30",
    "30M": "MINUTE_30",
    "30m": "MINUTE_30",
    "H1": "HOUR_1",
    "1H": "HOUR_1",
    "1h": "HOUR_1",
    "H2": "HOUR_2",
    "2H": "HOUR_2",
    "H4": "HOUR_4",
    "4H": "HOUR_4",
    "H6": "HOUR_6",
    "6H": "HOUR_6",
    "H12": "HOUR_12",
    "12H": "HOUR_12",
    "D1": "DAY_1",
    "1D": "DAY_1",
    "1d": "DAY_1",
    "W1": "WEEK_1",
    "1W": "WEEK_1",
    "MN1": "MONTH_1",
    "1MN": "MONTH_1",
}


class PoloniexExchangeAdapter:
    """Read-only market data adapter for Poloniex exchange."""

    BASE_URL = "https://api.poloniex.com"

    def __init__(self, session: requests.Session | None = None) -> None:
        self.session = session or create_http_session("HaruQuantAI-PoloniexAdapter/1.0")

    def fetch_bars(
        self,
        *,
        symbol: str,
        timeframe: str,
        start: int = 0,
        end: int = 0,
        count: int = 100,
        limit: int = 500,
        token: CancellationToken | None = None,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """Fetch historical candlestick bars from Poloniex markets candles endpoint."""
        sym = symbol.strip().upper()
        if "_" not in sym:
            if sym.endswith("USDT"):
                sym = f"{sym[:-4]}_USDT"
            elif sym.endswith("USD"):
                sym = f"{sym[:-3]}_USD"

        interval = INTERVAL_MAP.get(
            timeframe.strip().upper(),
            INTERVAL_MAP.get(timeframe.strip(), "MINUTE_1"),
        )
        url = f"{self.BASE_URL}/markets/{sym}/candles"

        target_limit = min(max(count, limit), 500)
        params: dict[str, Any] = {"interval": interval, "limit": target_limit}
        if start and start > 0:
            params["startTime"] = start * 1000 if start < 100_000_000_000 else start
        if end and end > 0:
            params["endTime"] = end * 1000 if end < 100_000_000_000 else end

        resp = execute_bounded_get(
            self.session,
            url,
            params=params,
            token=token,
            provider="crypto:poloniex",
        )
        if resp.status_code != 200:
            logger.warning(
                "%s: Poloniex returned status %d for %s",
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
            if not isinstance(item, list) or len(item) < 13:
                continue
            # Layout: [low, high, open, close, amount, quantity, buyTakerAmount, buyTakerQuantity, tradeCount, ts, weightedAverage, interval, startTime, closeTime]
            low_val, high_val, open_val, close_val, qty, start_ts = (
                item[0],
                item[1],
                item[2],
                item[3],
                item[5],
                item[12],
            )
            rows.append(
                {
                    "time": int(start_ts // 1000),
                    "open": float(open_val),
                    "high": float(high_val),
                    "low": float(low_val),
                    "close": float(close_val),
                    "tick_volume": int(float(qty)) if qty else 1,
                    "spread": 0,
                    "real_volume": int(float(qty)) if qty else 1,
                }
            )

        rows.sort(key=lambda r: r["time"])
        logger.debug("%s: Retrieved %d bars for %s", CANDLES_FR, len(rows), sym)
        return rows
