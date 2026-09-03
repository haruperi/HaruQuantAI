# MetaTrader 5 Connection

**Feature ID:** `FEAT-BRK-METATRADER`

## Domain

`broker`

## Purpose

Provide live MetaTrader 5 terminal connection and operational capabilities
mirroring the standard broker interface using the official `MetaTrader5` package
and database-stored credentials.

## Provides

`broker.provider.metatrader@1, broker.operations@1`

## Required Capabilities

None.

## Optional Capabilities

None.

## Configuration

| Key | Type | Required | Description |
|---|---|---|---|
| `database_path` | string | No | Path to SQLite central database for loading stored credentials. |
| `terminal_path` | string | No | Optional path to `terminal64.exe` executable. |
| `login` | integer | No | MT5 trading account login number. |
| `password` | string | No | MT5 trading account password. |
| `server` | string | No | MT5 broker server name. |
| `timeout` | integer | No | Terminal initialization timeout in seconds (default 30). |

Unknown keys and invalid types fail during configuration validation.

## Persistent State

`broker.metatrader` schema version 1 manages MT5 connection session preferences and channel parameters in `haruquantai.db`. Retention policy is `retain`.

## Runtime Effects

Mount initializes the MetaTrader 5 client service and provides `broker.provider.metatrader@1` and `broker.operations@1` in the feature context.

## Functional Requirements

- `FR 1: Direct MT5 Connection & Operations Mirror` (`client.py`): Provides direct MT5 operational functions (`get_terminal_info`, `get_account_info`, `get_symbol_info`, `get_position_info`, `get_order_info`, `get_history_order_info`, `get_history_deal_info`, `trade`) with real `MetaTrader5` library integration and automatic database credentials resolution, returning pure MT5 objects wrapped in `StandardResponse` envelopes without business logic.

## Failure Behavior

Terminal initialization errors and MT5 call failures are captured via `mt5.last_error()` and returned as `StandardResponse` failure envelopes with `status="error"` and structured error codes without unhandled process termination.

## Removal Behavior

Removing this feature disconnects active MT5 terminal sessions via `mt5.shutdown()` and withdraws the provider capability from the runtime context.
