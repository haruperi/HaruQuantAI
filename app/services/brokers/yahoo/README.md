# Yahoo Finance Provider

**Feature ID:** `FEAT-BRK-YAHOO`

## Domain

`broker`

## Purpose

Market data and fundamental provider adapter for Yahoo Finance.

## Provides

`broker.provider.yahoo@1, broker.operations@1`

## Required Capabilities

None.

## Optional Capabilities

None.

## Configuration

| Key | Type | Required | Description |
|---|---|---|---|
| `database_path` | string | No | Path to SQLite central database for loading stored preferences. |
| `timeout` | integer | No | HTTP request timeout in seconds (default 30). |

Unknown keys and invalid types fail during configuration validation.

## Persistent State

`broker.yahoo` schema version 1 manages Yahoo Finance preferences in `haruquantai.db`. Retention policy is `retain`.

## Runtime Effects

Mount initializes the Yahoo Finance client service and provides `broker.provider.yahoo@1` and `broker.operations@1` in the feature context.

## Functional Requirements

- `FR 1: Yahoo Finance Market Data Channel` (`client.py`): Implements symbol specifications, equities quotes, and OHLCV bars. Unsupported trading and account operations explicitly raise `NotImplementedError`.

## Failure Behavior

Data query failures raise explicit `RuntimeError` or `ValueError` exceptions. Unsupported capabilities raise `NotImplementedError`.

## Removal Behavior

Removing this feature withdraws Yahoo Finance provider capabilities from the registry.
