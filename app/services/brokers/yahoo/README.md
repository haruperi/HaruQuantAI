# FEAT-BRK-CONNECT_YAHOO — Yahoo Direct Broker Channel

> **Package:** `app/services/brokers/yahoo`
> **Status:** `Completed`
> **Capability:** `broker.provider.yahoo@1`
> **Port:** `app.contracts.broker.ports.ProviderBackend`

## Overview

`FEAT-BRK-CONNECT_YAHOO` provides research-only Yahoo Finance historical bars for
sandbox exploration and research workflows. It implements the ratified V3
`ProviderBackend` protocol and exposes `broker.provider.yahoo@1`.

## Features

- **Genuine historical bars**: Bounded OHLC retrieval mapped directly to `BrokerHistoryPage` and `BrokerBar`.
- **Pure boundaries**: No sibling feature imports, no `app.composition` imports, and no persistence.
- **Fail-closed sandbox validation**: Enforces `SANDBOX` environment and rejects any non-sandbox requests.
- **Deterministic unsupported mutations**: Rejects all order operations (`SUBMIT`, `CANCEL`, `MODIFY`, `JOURNAL`) and state reads (`READ_ACCOUNT`, `READ_TRADING_STATE`, `READ_MARKET`) with `BROKER_PROFILE_UNSUPPORTED`.
- **Circuit-broken transport**: Dedicated `_YahooCircuitBreaker` guarding yfinance calls run off the event loop.

## Configuration

```python
from app.services.brokers.yahoo.config import YahooConfig

config = YahooConfig(
    probe_symbol="SPY",
    request_timeout_sec=30.0,
    circuit_failure_threshold=5,
    circuit_recovery_timeout_sec=30.0,
    circuit_half_open_max_calls=1,
    environment="SANDBOX",
)
```
