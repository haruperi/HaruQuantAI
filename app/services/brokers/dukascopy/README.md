# FEAT-BRK-CONNECT_DUKASCOPY — Dukascopy Direct Broker Channel

> **Package:** `app/services/brokers/dukascopy`
> **Status:** `Completed`
> **Capability:** `broker.provider.dukascopy@1`
> **Port:** `app.contracts.broker.ports.ProviderBackend`

## Overview

`FEAT-BRK-CONNECT_DUKASCOPY` provides research-only Dukascopy market datafeed historical BID candles
and ticks for sandbox exploration and quantitative research workflows. It implements the ratified V3
`ProviderBackend` protocol and exposes `broker.provider.dukascopy@1`.

## Features

- **Genuine bounded ticks & BID candles**: Bounded retrieval mapped directly to `BrokerHistoryPage` and `BrokerBar`.
- **Pure boundaries**: No sibling feature imports, no `app.composition` imports, and no persistence.
- **Fail-closed sandbox validation**: Enforces `SANDBOX` environment and rejects any non-sandbox requests.
- **Deterministic unsupported mutations**: Rejects all order operations (`SUBMIT`, `CANCEL`, `MODIFY`, `JOURNAL`) and state reads (`READ_ACCOUNT`, `READ_TRADING_STATE`, `READ_MARKET`) with `BROKER_PROFILE_UNSUPPORTED`.
- **Circuit-broken transport**: Dedicated transport circuit breaker guarding web-chart JSONP calls run off the event loop.

## Configuration

```python
from app.services.brokers.dukascopy.config import DukascopyConfig

config = DukascopyConfig(
    probe_symbol="EURUSD",
    request_timeout_sec=30.0,
    circuit_failure_threshold=5,
    circuit_recovery_timeout_sec=30.0,
    circuit_half_open_max_calls=1,
    environment="SANDBOX",
)
```
