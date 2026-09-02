# Broker Operations

**Feature ID:** `FEAT-BRK-OPERATIONS`

## Domain

`broker`

## Purpose

Provide standard broker-neutral operational functions without business logic,
bridging terminal connectivity, account data, market data subscriptions, orders,
deals, positions, and trade operations.

## Provides

`broker.operations@1`

## Required Capabilities

None.

## Optional Capabilities

None.

## Configuration

| Key | Type | Required | Description |
|---|---|---|---|
| `database_path` | string | No | Optional SQLite database path for operations state and caching. |

Unknown keys and non-string values are rejected during configuration parsing.

## Persistent State

`broker.operations` schema version 1 retains operational subscriptions and execution receipts in the central `haruquantai.db` database. Retention policy is `retain`: removing the feature preserves execution history.

## Runtime Effects

Mount stages the `broker.operations@1` capability provider into the feature scope. Operations open bounded queries and maintain live in-memory subscription maps.

## Functional Requirements

- `FR 1: Broker Environment Properties` (`_terminal_info.py`): Terminal connection state, ping, platform info, and provider specifications.
- `FR 2: Account Properties and State` (`_account_info.py`): Account properties, balances, permissions, and equity snapshots.
- `FR 3: Symbol Properties and Market Data` (`_symbol_info.py`): Symbol specifications, quotes, spreads, tick data, historical bars, and market data subscriptions.
- `FR 4: Pending and Active Orders` (`_order_info.py`): Active orders, ticket lookups, and pre-trade margin/volume checks.
- `FR 5: Historical Orders` (`_history_order_info.py`): Historical order listings and individual historical orders.
- `FR 6: Deals and Transactions` (`_deals_info.py`): Executed deal records and account financial transactions.
- `FR 7: Open Positions` (`_positions_info.py`): Open trading positions and individual position lookups.
- `FR 8: Trade Execution Functions` (`_trade.py`): Order placement, modification, cancellation, position modification, position closing, and margin/profit calculations.
- `FR 9: Execution Bridge` (`execute.py`): Entry point bridging all operations and hosting `BrokerOperationsService`.

## Failure Behavior

Invalid symbol lookups, unrecognized order IDs, and impossible trade actions return structured failure responses or raise explicit `ValueError` without unhandled crashes.

## Removal Behavior

Removing this feature withdraws the `broker.operations@1` capability provider from runtime scope. External broker connections are closed cleanly.
