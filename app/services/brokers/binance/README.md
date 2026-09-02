# Binance Provider Connection

**Feature ID:** `FEAT-BRK-BINANCE`

## Domain

`broker`

## Purpose

Direct provider connection and operational adapter for Binance Crypto Exchange.

## Provides

`broker.provider.binance@1, broker.operations@1`

## Required Capabilities

None.

## Optional Capabilities

None.

## Configuration

| Key | Type | Required | Description |
|---|---|---|---|
| `database_path` | string | No | Path to SQLite central database for loading stored credentials. |
| `api_key` | string | No | Binance API key. |
| `api_secret` | string | No | Binance API secret. |
| `testnet` | boolean | No | Whether to connect to Binance Testnet (default false). |
| `timeout` | integer | No | Connection timeout in seconds (default 30). |

Unknown keys and invalid types fail during configuration validation.

## Persistent State

`broker.binance` schema version 1 manages Binance connection parameters in `haruquantai.db`. Retention policy is `retain`.

## Runtime Effects

Mount initializes the Binance client service and provides `broker.provider.binance@1` and `broker.operations@1` in the feature context.

## Functional Requirements

- `FR 1: Binance Provider Channel` (`client.py`): Implements standard broker operational functions (terminal info, multi-asset balances, crypto quotes, orders, deals, positions, trade execution) with fail-closed error handling.

## Failure Behavior

Connection and query failures raise explicit `RuntimeError` or `ValueError` exceptions without silent fallback data.

## Removal Behavior

Removing this feature closes active Binance sessions and withdraws provider capabilities from the registry.
