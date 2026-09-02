# cTrader Provider Connection

**Feature ID:** `FEAT-BRK-CTRADER`

## Domain

`broker`

## Purpose

Direct provider connection and operational adapter for Spotware cTrader OpenAPI.

## Provides

`broker.provider.ctrader@1, broker.operations@1`

## Required Capabilities

None.

## Optional Capabilities

None.

## Configuration

| Key | Type | Required | Description |
|---|---|---|---|
| `database_path` | string | No | Path to SQLite central database for loading stored credentials. |
| `client_id` | string | No | Spotware OpenAPI application Client ID. |
| `client_secret` | string | No | Spotware OpenAPI application Client Secret. |
| `access_token` | string | No | Spotware OpenAPI OAuth access token. |
| `account_id` | string | No | Target cTrader account identifier. |
| `live` | boolean | No | Whether to connect to live environment (default false). |
| `timeout` | integer | No | Connection timeout in seconds (default 30). |

Unknown keys and invalid types fail during configuration validation.

## Persistent State

`broker.ctrader` schema version 1 manages cTrader connection parameters in `haruquantai.db`. Retention policy is `retain`.

## Runtime Effects

Mount initializes the cTrader client service and provides `broker.provider.ctrader@1` and `broker.operations@1` in the feature context.

## Functional Requirements

- `FR 1: cTrader Provider Channel` (`client.py`): Implements standard broker operational functions (terminal info, account info, market data, orders, deals, positions, trade execution) with fail-closed error handling.

## Failure Behavior

Connection and query failures raise explicit `RuntimeError` or `ValueError` exceptions without silent fallback data.

## Removal Behavior

Removing this feature closes active cTrader sessions and withdraws provider capabilities from the registry.
