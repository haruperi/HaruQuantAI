"""Coinbase public REST market data adapter for cryptocurrency historical candles.

Description:
    Implements a bounded, read-only historical candlestick adapter for Coinbase
    (migrated from legacy Coinbase Pro to current official Coinbase Exchange API).
    Conforms to the `data.provider` contract with granularity translation,
    cooperative cancellation, and normalized bar representations.

Purpose:
    FEAT-BROKER-CRYPTO-COINBASE: Coinbase exchange historical market data adapter.

Key Capabilities:
    - FR-BROKER-COINBASE-CANDLES: Fetch and normalize historical candles from Coinbase API.
      Associated: `CoinbaseExchangeAdapter.fetch_bars()`
      Logging: Emits DEBUG when requesting candles and logging received record counts.

Python API Usage:
    ```python
    from app.services.brokers.exchanges.coinbase import CoinbaseExchangeAdapter

    adapter = CoinbaseExchangeAdapter()
    bars = adapter.fetch_bars(symbol="BTC-USD", timeframe="1h", count=50)
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/services/brokers/test_brokers_rest_and_cdn_providers.py --no-cov
    ```
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import requests
from app.host.logging import get_logger
from app.services.brokers._http import create_http_session, execute_bounded_get
from app.services.brokers.capabilities import CancellationToken

logger = get_logger(__name__)

CANDLES_FR = "FR-BROKER-COINBASE-CANDLES"

__all__ = ["CoinbaseExchangeAdapter"]

GRANULARITY_MAP: dict[str, int] = {
    "M1": 60,
    "1M": 60,
    "1m": 60,
    "M5": 300,
    "5M": 300,
    "5m": 300,
    "M15": 900,
    "15M": 900,
    "15m": 900,
    "H1": 3600,
    "1H": 3600,
    "1h": 3600,
    "H6": 21600,
    "6H": 21600,
    "6h": 21600,
    "D1": 86400,
    "1D": 86400,
    "1d": 86400,
}


class CoinbaseExchangeAdapter:
    """Read-only market data adapter for Coinbase exchange."""

    BASE_URL = "https://api.exchange.coinbase.com"

    def __init__(self, session: requests.Session | None = None) -> None:
        self.session = session or create_http_session("HaruQuantAI-CoinbaseAdapter/1.0")

    def fetch_bars(
        self,
        *,
        symbol: str,
        timeframe: str,
        start: int = 0,
        end: int = 0,
        count: int = 100,
        limit: int = 300,
        token: CancellationToken | None = None,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """Fetch historical candlestick bars from Coinbase products candles endpoint."""
        sym = symbol.strip().upper()
        if "-" not in sym:
            if sym.endswith("USDT"):
                sym = f"{sym[:-4]}-USDT"
            elif sym.endswith("USD"):
                sym = f"{sym[:-3]}-USD"

        gran = GRANULARITY_MAP.get(
            timeframe.strip().upper(), GRANULARITY_MAP.get(timeframe.strip(), 60)
        )
        url = f"{self.BASE_URL}/products/{sym}/candles"

        params: dict[str, Any] = {"granularity": gran}
        if start and start > 0:
            ts = start if start < 100_000_000_000 else start // 1000
            params["start"] = datetime.fromtimestamp(ts, tz=UTC).isoformat()
        if end and end > 0:
            ts = end if end < 100_000_000_000 else end // 1000
            params["end"] = datetime.fromtimestamp(ts, tz=UTC).isoformat()

        resp = execute_bounded_get(
            self.session,
            url,
            params=params,
            token=token,
            provider="crypto:coinbase",
        )
        if resp.status_code != 200:
            logger.warning(
                "%s: Coinbase returned status %d for %s",
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
            # Layout: [time, low, high, open, close, volume]
            t, low_val, high_val, open_val, close_val, vol = (
                item[0],
                item[1],
                item[2],
                item[3],
                item[4],
                item[5],
            )
            rows.append(
                {
                    "time": int(t),
                    "open": float(open_val),
                    "high": float(high_val),
                    "low": float(low_val),
                    "close": float(close_val),
                    "tick_volume": int(vol) if vol else 1,
                    "spread": 0,
                    "real_volume": int(vol) if vol else 1,
                }
            )

        rows.sort(key=lambda r: r["time"])
        target_count = count if count > 0 else limit
        if target_count and len(rows) > target_count:
            rows = rows[-target_count:]

        logger.debug("%s: Retrieved %d bars for %s", CANDLES_FR, len(rows), sym)
        return rows
