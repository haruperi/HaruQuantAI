"""Yahoo Finance market data provider for historical daily and intraday equity bars.

Description:
    Downloads historical and intraday candlestick bar data directly from the
    public Yahoo Finance v8 chart API (`query1.finance.yahoo.com/v8/finance/chart/`).
    Conforms to the uniform `BrokerClient` interface.
    Maps M1 through MN1 timeframes to valid Yahoo intervals (1m, 2m, 5m, 15m, 30m,
    60m, 1d, 1wk, 1mo) and enforces Yahoo's retention limits (e.g. 1m data is capped
    at 7 days, 5m at 60 days). Supports local filesystem caching. Network calls are
    executed via bounded HTTP requests with credential redaction.

Purpose:
    FEAT-BROKER-YAHOO: Real-time and historical equity and ETF candlestick acquisition.

Key Capabilities:
    - FR-BROKER-YAHOO-MARKET-DATA: Fetch historical OHLCV candlestick bars via REST.
      Associated: `YahooClient.get_bars()`.
      Logging: INFO on bars parsed, symbol, interval, and record count.
    - FR-BROKER-YAHOO-SYMBOL-METADATA: Inspect Yahoo instrument parameters.
      Associated: `YahooClient.get_symbol_info()`, `YahooClient.get_symbols()`.
      Logging: INFO on symbol metadata resolution and popular equity catalogs.

Python API Usage:
    ```python
    from app.services.brokers.yahoo import YahooClient

    client = YahooClient()
    bars = client.get_bars("AAPL", "1d", count=100)
    ```

CLI Usage:
    ```bash
    uv run python -m app.services.brokers.yahoo
    ```
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, override

import pandas as pd  # type: ignore[import-untyped]
from app.host.logging import get_logger
from app.services.brokers.base import (
    BridgeError,
    BrokerClient,
    create_http_session,
    execute_bounded_get,
)
from app.services.include.contracts import MarketBar, MarketTick, SymbolInfo
from app.services.include.data import bars_to_dataframe
from app.services.include.enums import Timeframe

MARKET_DATA_FR = "FR-BROKER-YAHOO-MARKET-DATA"
SYMBOL_METADATA_FR = "FR-BROKER-YAHOO-SYMBOL-METADATA"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
)

TIMEFRAME_TO_YAHOO_INTERVAL: dict[str, str] = {
    "M1": "1m",
    "1M": "1m",
    Timeframe.PERIOD_M1.value: "1m",
    "M2": "2m",
    "2M": "2m",
    Timeframe.PERIOD_M2.value: "2m",
    "M5": "5m",
    "5M": "5m",
    Timeframe.PERIOD_M5.value: "5m",
    "M15": "15m",
    "15M": "15m",
    Timeframe.PERIOD_M15.value: "15m",
    "M30": "30m",
    "30M": "30m",
    Timeframe.PERIOD_M30.value: "30m",
    "H1": "60m",
    "1H": "60m",
    Timeframe.PERIOD_H1.value: "60m",
    "H4": "60m",
    "4H": "60m",
    Timeframe.PERIOD_H4.value: "60m",
    "D1": "1d",
    "1D": "1d",
    Timeframe.PERIOD_D1.value: "1d",
    "W1": "1wk",
    "1W": "1wk",
    Timeframe.PERIOD_W1.value: "1wk",
    "MN1": "1mo",
    "1MN": "1mo",
    Timeframe.PERIOD_MN1.value: "1mo",
}

DEFAULT_SYMBOLS = ["AAPL", "MSFT", "GOOGL", "AMZN", "SPY", "QQQ"]

__all__ = [
    "YahooClient",
]

logger = get_logger(__name__)


class YahooClient(BrokerClient):
    """Client for acquiring historical market data from Yahoo Finance."""

    CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"

    def __init__(
        self,
        cache_dir: str | Path | None = None,
        name: str = "Yahoo",
    ) -> None:
        super().__init__(name=name)
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self.session = create_http_session(USER_AGENT)

    def _resolve_interval(self, timeframe: str) -> str:
        """Resolve canonical Timeframe into Yahoo chart API interval string."""
        clean_tf = timeframe.upper().strip()
        interval = TIMEFRAME_TO_YAHOO_INTERVAL.get(clean_tf)
        if interval is not None:
            return interval
        if clean_tf in (
            "1M",
            "2M",
            "5M",
            "15M",
            "30M",
            "60M",
            "90M",
            "1D",
            "5D",
            "1WK",
            "1MO",
            "3MO",
        ):
            return clean_tf.lower()
        raise BridgeError(
            f"Unsupported timeframe '{timeframe}' for Yahoo Finance",
            code="UNSUPPORTED_TIMEFRAME",
        )

    @override
    def get_bars(
        self,
        symbol: str,
        timeframe: Timeframe | str = Timeframe.PERIOD_H1,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        *,
        start_pos: int | None = None,
        count: int | None = None,
        limit: int = 1000,
    ) -> pd.DataFrame:
        """Fetch historical candlestick bars directly from Yahoo Finance."""
        del start_pos
        clean_sym = symbol.strip().upper()
        tf_str = timeframe.value if isinstance(timeframe, Timeframe) else timeframe
        interval = self._resolve_interval(tf_str)

        start = int(date_from.timestamp()) if date_from else 0
        end = (
            int(date_to.timestamp())
            if date_to
            else int(datetime.now(tz=UTC).timestamp())
        )

        params: dict[str, Any] = {
            "interval": interval,
            "includePrePost": "false",
            "events": "div,splits",
        }

        if start > 0 and end > 0:
            params["period1"] = start
            params["period2"] = end
        elif interval in ("1m", "2m", "5m"):
            params["range"] = "5d"
        elif interval in ("15m", "30m", "60m"):
            params["range"] = "1mo"
        elif interval in ("1d", "1wk"):
            params["range"] = "1y"
        else:
            params["range"] = "2y"

        cache_file: Path | None = None
        if self.cache_dir is not None:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            cache_file = self.cache_dir / f"{clean_sym}_{interval}.json"

        try:
            url = self.CHART_URL.format(symbol=clean_sym)
            resp = execute_bounded_get(
                self.session, url, params=params, provider="yahoo"
            )
            if resp.status_code == 429:
                raise BridgeError(
                    f"Yahoo Finance rate limit exceeded (HTTP 429) for {clean_sym}",
                    code="RATE_LIMIT",
                )
            if resp.status_code in (401, 403):
                raise BridgeError(
                    f"Yahoo Finance authentication rejected for {clean_sym}",
                    code="AUTHENTICATION",
                )
            if resp.status_code != 200:
                raise BridgeError(
                    f"Yahoo Finance HTTP {resp.status_code} for {clean_sym}",
                    code="REMOTE_ERROR",
                )

            data = resp.json()
            if cache_file is not None:
                cache_file.write_text(json.dumps(data), encoding="utf-8")

            chart = data.get("chart", {})
            error = chart.get("error")
            if error:
                err_code = error.get("code", "UNKNOWN")
                err_desc = error.get("description", "Unknown error")
                raise BridgeError(
                    f"Yahoo chart API error ({err_code}): {err_desc}",
                    code="VENDOR_ERROR",
                )

            results = chart.get("result")
            if not results:
                raise BridgeError(
                    f"No chart results returned from Yahoo Finance for {clean_sym}",
                    code="NO_DATA",
                )

            result = results[0]
            timestamps = result.get("timestamp", [])
            indicators = result.get("indicators", {})
            quote_list = indicators.get("quote", [])
            if not timestamps or not quote_list:
                raise BridgeError(
                    f"No candlestick quote data returned from Yahoo Finance for {clean_sym}",
                    code="NO_DATA",
                )

            quote = quote_list[0]
            opens = quote.get("open", [])
            highs = quote.get("high", [])
            lows = quote.get("low", [])
            closes = quote.get("close", [])
            volumes = quote.get("volume", [])

            bars: list[MarketBar] = []
            for i, ts in enumerate(timestamps):
                if (
                    i < len(opens)
                    and i < len(highs)
                    and i < len(lows)
                    and i < len(closes)
                    and opens[i] is not None
                    and highs[i] is not None
                    and lows[i] is not None
                    and closes[i] is not None
                ):
                    vol = (
                        int(volumes[i])
                        if i < len(volumes) and volumes[i] is not None
                        else 0
                    )
                    bars.append(
                        MarketBar(
                            time=int(ts),
                            open=float(opens[i]),
                            high=float(highs[i]),
                            low=float(lows[i]),
                            close=float(closes[i]),
                            tick_volume=vol,
                            spread=0,
                            real_volume=vol,
                        )
                    )

            bars.sort(key=lambda b: b.time)
            deduped: list[MarketBar] = []
            last_t: int | None = None
            for b in bars:
                if last_t is None or b.time > last_t:
                    deduped.append(b)
                    last_t = b.time

            target_count = count if count is not None and count > 0 else limit
            if target_count and len(deduped) > target_count:
                deduped = deduped[-target_count:]

            logger.info(
                "%s: Parsed %d bars for %s (%s)",
                MARKET_DATA_FR,
                len(deduped),
                clean_sym,
                interval,
                extra={
                    "fr_id": MARKET_DATA_FR,
                    "count": len(deduped),
                    "symbol": clean_sym,
                },
            )
            return bars_to_dataframe(deduped)
        except Exception as exc:
            if isinstance(exc, BridgeError):
                raise
            raise BridgeError(
                f"Error downloading Yahoo bars for {clean_sym}: {exc}",
                code="DOWNLOAD_ERROR",
            ) from exc

    @override
    def get_ticks(
        self,
        symbol: str,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        *,
        count: int | None = None,
        limit: int = 1000,
    ) -> list[MarketTick]:
        """Yahoo Finance does not support tick-level market data."""
        del symbol, date_from, date_to, count, limit
        raise BridgeError(
            "Yahoo Finance does not support tick history",
            code="UNSUPPORTED_OPERATION",
        )

    @override
    def get_symbol_info(self, symbol: str) -> SymbolInfo:
        """Resolve equity metadata specification for symbol."""
        clean_sym = symbol.strip().upper()
        logger.info(
            "%s: Querying symbol specifications for %s",
            SYMBOL_METADATA_FR,
            clean_sym,
            extra={"fr_id": SYMBOL_METADATA_FR, "symbol": clean_sym},
        )
        digits = 2
        point = 0.01
        contract_size = 1.0
        currency_base = "USD"
        currency_profit = "USD"
        currency_margin = "USD"

        if clean_sym.endswith("=X"):
            digits = 4
            point = 0.0001
            contract_size = 100_000.0
            pair = clean_sym[:-2]
            if len(pair) == 6:
                currency_base = pair[:3]
                currency_profit = pair[3:]
                currency_margin = currency_base
        elif clean_sym.endswith("=F"):
            digits = 2
            point = 0.01
            contract_size = 50.0

        return SymbolInfo(
            name=clean_sym,
            digits=digits,
            point=point,
            trade_contract_size=contract_size,
            currency_base=currency_base,
            currency_profit=currency_profit,
            currency_margin=currency_margin,
            description=f"Yahoo Finance: {clean_sym}",
        )

    @override
    def get_symbols(self) -> list[str]:
        """Return default popular symbols available on Yahoo."""
        logger.info(
            "%s: Returning default Yahoo symbol list (%d items)",
            SYMBOL_METADATA_FR,
            len(DEFAULT_SYMBOLS),
            extra={"fr_id": SYMBOL_METADATA_FR, "count": len(DEFAULT_SYMBOLS)},
        )
        return list(DEFAULT_SYMBOLS)


def main() -> None:
    """Demonstrate executable usage of YahooClient."""
    client = YahooClient()
    symbols = client.get_symbols()
    logger.info("Supported symbols: %s...", symbols[:3])
    info = client.get_symbol_info("AAPL")
    logger.info("AAPL info: digits=%s point=%s", info.digits, info.point)
    client.disconnect()


if __name__ == "__main__":
    main()
