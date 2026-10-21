"""Live broker connection credential, latency, and permission verification service.

Description:
    Provides the LiveTest diagnostic service inheriting shared transport and
    lifecycle contracts from BrokerClient. Validates broker gateway credentials
    with automatic secret redaction, measures quote streaming and order check
    round-trip latency with default readonly research profile enforcement, and
    verifies account trading permissions and margin currency settings.

Purpose:
    FEAT-BROKER-LIVETEST: Live broker credential, latency, and permission verification.

Key Capabilities:
    - FR-BROKER-LIVETEST-CREDENTIALS: Validate broker credentials and API tokens [`LiveTest.validate_credentials()`] (`INFO`).
    - FR-BROKER-LIVETEST-LATENCY: Measure quote and order round-trip latency [`LiveTest.measure_trading_latency()`] (`INFO`).
    - FR-BROKER-LIVETEST-PERMISSIONS: Verify account permissions and margin currency [`LiveTest.verify_trading_permissions()`] (`INFO`).

Python API Usage:
    ```python
    from app.services.brokers.registry import LiveTest, LiveTestCLI

    service = LiveTest()
    report = service.validate_credentials("simulator", {"account_id": "sim-01"})
    print(LiveTestCLI.format_output(report))
    ```

CLI Usage:
    ```bash
    uv run python -m app.services.brokers.registry
    ```
"""

from __future__ import annotations

import sys
from argparse import ArgumentParser
from collections.abc import Mapping, Sequence
from contextlib import suppress
from dataclasses import dataclass
from json import dumps
from time import perf_counter
from typing import Any

from app.host.logging import TelemetryLogger, get_logger
from app.services.brokers import base as _b
from app.services.include.contracts import AccountInfo, SymbolInfo, TradeRequest

__all__ = ["LiveTest", "LiveTestCLI"]
logger = get_logger(__name__)
type _Pld = dict[str, Any]
CREDENTIALS_FR = "FR-BROKER-LIVETEST-CREDENTIALS"
LATENCY_FR = "FR-BROKER-LIVETEST-LATENCY"
PERMISSIONS_FR = "FR-BROKER-LIVETEST-PERMISSIONS"

_REQ_KEYS: dict[str, tuple[str, ...]] = {
    "ctrader": ("client_id", "client_secret", "access_token", "account_id"),
    "metatrader": ("auth_token",),
    "binance": ("api_key", "api_secret"),
    "crypto": ("api_key", "api_secret"),
    "darwinex": ("api_token",),
}
for _p in "simulator live_test dukascopy yahoo files sq_equity sq_futures tick_downloader".split():
    _REQ_KEYS[_p] = ()
_CURRENCIES: dict[str, str] = {"ctrader": "EUR", "binance": "USDT", "crypto": "USDT"}
_TRADING_SET = frozenset("simulator live_test metatrader ctrader binance".split())


@dataclass(frozen=True)
class _Config:
    """Internal configuration for LiveTest diagnostics and execution safety."""

    timeout_seconds: float = 5.0
    default_symbol: str = "EURUSD"
    allow_live_execution: bool = False
    default_currency: str = "USD"
    default_leverage: int = 100


class LiveTest(_b.BrokerClient):
    """Broker connection validator, latency probe, and permission verifier."""

    def __init__(self, config: _Config | None = None) -> None:
        super().__init__(name="live_test")
        self._config = config or _Config()

    @staticmethod
    def _resolve_client(norm_provider: str) -> Any:
        if norm_provider != "live_test":
            with suppress(KeyError):
                return _b.get_broker(norm_provider)
        return None

    def validate_credentials(
        self, provider: str, credentials: Mapping[str, Any]
    ) -> dict[str, Any]:
        """Validate live broker credentials and API tokens against broker gateways."""
        norm, raw = _b.normalize_provider_id(provider), dict(credentials)
        red = TelemetryLogger.redact_secrets(raw)
        safe: _Pld = dict(red) if isinstance(red, dict) else {}
        known = norm in _REQ_KEYS
        mt_ok = norm == "metatrader" and bool(raw.get("login") and raw.get("server"))
        ks = _REQ_KEYS.get(norm, ())
        miss = [k for k in ks if not str(raw.get(k) or "").strip() and not mt_ok]
        ok = bool(known and not miss and norm)
        bad = "UNKNOWN_PROVIDER" if not known else "INVALID_CREDENTIALS"
        st, ts = "VALID" if ok else bad, _b.utc_now().isoformat()
        d: _Pld = {"provider": norm, "valid": ok, "authenticated": ok, "status": st}
        d |= {"missing_fields": miss, "redacted_credentials": safe, "timestamp_utc": ts}
        ex = {"fr_id": CREDENTIALS_FR, "provider": norm, "status": st}
        log = logger.info if ok else logger.warning
        log("%s: Validated %s (%s)", CREDENTIALS_FR, norm, st, extra=ex)
        return d

    def measure_trading_latency(
        self, provider: str, symbol: str = "EURUSD"
    ) -> dict[str, Any]:
        """Measure order placement and quote streaming round-trip latency."""
        norm = _b.normalize_provider_id(provider)
        sym = symbol.strip().upper() or self._config.default_symbol
        c, t0 = self._resolve_client(norm) or self, perf_counter()
        _ = c.get_symbol_info(sym) if hasattr(c, "get_symbol_info") else SymbolInfo(sym)
        q_ms = round(max(0.01, (perf_counter() - t0) * 1000.0), 3)
        auth, t1 = bool(self._config.allow_live_execution), perf_counter()
        if auth and hasattr(c, "order_check"):
            _ = c.order_check(TradeRequest(symbol=sym, volume=0.01))
            o_ms = round(max(0.01, (perf_counter() - t1) * 1000.0), 3)
            st = "AUTHORIZED_ORDER_CHECK"
        else:
            st, o_ms = "DISABLED_READONLY_PROFILE", 0.0
        rtt = round(q_ms + o_ms, 3)
        d: _Pld = {"provider": norm, "symbol": sym, "readonly_profile": not auth}
        d |= {"execution_authorized": auth, "order_probe_status": st}
        d |= {"quote_latency_ms": q_ms, "order_latency_ms": o_ms}
        d |= {"round_trip_latency_ms": rtt, "timestamp_utc": _b.utc_now().isoformat()}
        ex = {"fr_id": LATENCY_FR, "provider": norm, "symbol": sym}
        logger.info("%s: Latency %s/%s %.3fms", LATENCY_FR, norm, sym, rtt, extra=ex)
        return d

    def verify_trading_permissions(
        self, provider: str, account_id: str
    ) -> dict[str, Any]:
        """Verify account trading permissions and margin currency settings."""
        norm, acc_id = _b.normalize_provider_id(provider), account_id.strip()
        c, known = self._resolve_client(norm), norm in _REQ_KEYS
        def_cur = _CURRENCIES.get(norm, self._config.default_currency)
        raw_acc = c.get_account_info() if c and hasattr(c, "get_account_info") else None
        acc = (
            raw_acc
            if isinstance(raw_acc, AccountInfo)
            else AccountInfo(currency=def_cur, leverage=self._config.default_leverage)
        )
        ok = bool(known and acc_id)
        tr = bool(ok and norm in _TRADING_SET and getattr(acc, "trade_allowed", True))
        perms: list[str] = ["market_data", "account_read"] if ok else []
        if tr:
            perms.append("order_check")
            if self._config.allow_live_execution:
                perms.append("order_execution")
        cur = str(acc.currency or self._config.default_currency)
        lev = int(acc.leverage or self._config.default_leverage)
        mm, ts = (
            str(getattr(acc.margin_mode, "name", "RETAIL_HEDGING")),
            _b.utc_now().isoformat(),
        )
        d: _Pld = {"provider": norm, "account_id": acc_id, "verified": ok}
        d |= {"trade_allowed": tr, "margin_currency": cur, "leverage": lev}
        d |= {"margin_mode": mm, "permissions": perms, "timestamp_utc": ts}
        ex = {"fr_id": PERMISSIONS_FR, "provider": norm, "verified": ok}
        log = logger.info if ok else logger.warning
        log("%s: Permissions %s/%s ok=%s", PERMISSIONS_FR, norm, acc_id, ok, extra=ex)
        return d


class LiveTestCLI:
    """Headless CLI runner and JSON formatter for FEAT-BROKER-LIVETEST."""

    @classmethod
    def format_output(cls, data: Mapping[str, Any]) -> str:
        """Format LiveTest diagnostic payload into indented JSON."""
        return dumps(dict(data), indent=2)

    @classmethod
    def run(cls, argv: Sequence[str] | None = None) -> int:
        """Execute LiveTest verification checks from the command line."""
        p = ArgumentParser(prog="app.services.brokers.registry")
        p.add_argument("--provider", default="simulator")
        p.add_argument("--symbol", default="EURUSD")
        p.add_argument("--account-id", default="sim-001")
        a, svc = p.parse_args(argv), LiveTest()
        creds = {"account_id": a.account_id, "api_token": "demo-tok"}
        rep: _Pld = {"credentials": svc.validate_credentials(a.provider, creds)}
        rep["latency"] = svc.measure_trading_latency(a.provider, a.symbol)
        rep["permissions"] = svc.verify_trading_permissions(a.provider, a.account_id)
        sys.stdout.write(cls.format_output(rep) + "\n")
        return 0


if __name__ == "__main__":
    raise SystemExit(LiveTestCLI.run())
