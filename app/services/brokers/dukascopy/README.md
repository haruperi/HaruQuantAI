# Dukascopy Provider Connection

**Feature ID:** `FEAT-BRK-DUKASCOPY`

## Domain

`broker`

## Purpose

Direct provider connection and operational adapter for Dukascopy Bank / JForex.

## Provides

`broker.provider.dukascopy@1, broker.operations@1`

## Required Capabilities

None.

## Optional Capabilities

None.

## Configuration

| Key | Type | Required | Description |
|---|---|---|---|
| `database_path` | string | No | Path to SQLite central database for loading stored credentials. |
| `username` | string | No | Dukascopy account username. |
| `password` | string | No | Dukascopy account password. |
| `account_id` | string | No | Target account identifier. |
| `live` | boolean | No | Whether to connect to live environment (default false). |
| `timeout` | integer | No | Connection timeout in seconds (default 30). |

Unknown keys and invalid types fail during configuration validation.

## Persistent State

`broker.dukascopy` schema version 1 manages Dukascopy connection parameters in `haruquantai.db`. Retention policy is `retain`.

## Runtime Effects

Mount initializes the Dukascopy client service and provides `broker.provider.dukascopy@1` and `broker.operations@1` in the feature context.

## Functional Requirements

- `FR 1: Dukascopy Provider Channel` (`client.py`): Implements standard broker operational functions (terminal info, account info, market data, orders, deals, positions, trade execution) with fail-closed error handling.

## Failure Behavior

Connection and query failures raise explicit `RuntimeError` or `ValueError` exceptions without silent fallback data.

## Removal Behavior

Removing this feature closes active Dukascopy connections and withdraws provider capabilities from the registry.
