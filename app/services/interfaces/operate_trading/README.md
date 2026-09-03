# Operate Trading Gateway (`FEAT-IFACE-OPERATE_TRADING`)

> **Package:** `app/services/interfaces/operate_trading/`
> **System role:** External boundary gateway exposing governed trading operations, readiness preflights, session controls, and ordered event streams.
> **Status:** `Completed` — Phase 7
> **Provided capability:** `interfaces.operate-trading@1`

---

## 1. Purpose & Boundary

Translates external HTTP/ASGI requests for trading operations (`MANAGE_SESSION`, `READINESS`, `PREVIEW_ACTION`, `EMERGENCY`, `MARKET_DATA`, `OPERATOR_ANALYTICS`) into typed `OperateTradingRequest` records.

### Core Architectural Invariants
- **No direct broker calls**: D-IFACE never imports broker implementations directly or queries MT5/cTrader/Binance directly.
- **Strict capability dependency**: Resolves upstream capabilities (`trading.account-operations@1`, `trading.dispatch-orders@1`, `trading.manage-trading-sessions@1`) through `FeatureContext`.
- **Fail-closed safety**: If an upstream capability provider is unmounted or missing, the gateway responds with the canonical `CAPABILITY_UNAVAILABLE` error envelope without inventing execution fills or trading outcomes.
- **Ordered streaming**: Exposes ordered domain events with replay bounds and resumption cursors.

## 2. Manifest & Configuration

Declared in `manifest.py`:
- `feature_id = "FEAT-IFACE-OPERATE_TRADING"`
- `provides = frozenset({OPERATE_TRADING_CAPABILITY})`
- `config_keys = frozenset({"default_account_id", "max_order_quantity"})`

Configuration defined in `config.py`:
- `default_account_id: str` (default: `"default"`)
- `max_order_quantity: float` (default: `1000.0`)
Unknown configuration keys fail closed at mount.
