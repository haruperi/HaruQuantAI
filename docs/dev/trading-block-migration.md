# Order and StrategyControl canonical block migration

## Ownership

All 12 operations in donor `SQ/Blocks/Order` and all 25 operations in
`SQ/Blocks/StrategyControl` have one canonical decorated Python function per file
in `app/include/blocks/order` and `app/include/blocks/strategy_control`.
The complete source/ID mapping is in
`fixtures/trading-block-migration-manifest.json`.

Every selectable function has a `BlockSpec` and `@block` annotation. Order blocks
use `ExecutionKind.ORDER`; boolean queries use `CONDITION`; numeric queries use
`EXPRESSION`. Ports distinguish runtime inputs from configurable scalar arguments.
The reserved `context` input is supplied by the execution runner, not serialized
as user configuration. Sources are independently discoverable; package initializers
perform no eager sibling imports, registration or execution.

The donor files carry `@IgnoreInBuilder`; these blocks are available for explicit
selection/execution, with `is_generation_eligible=False`. Automatic-generator
policy and typed strategy-document integration remain separate planned work.
No current-state query claims to reconstruct a historical account snapshot.

## Runtime boundary

`order/runtime.py` defines structural protocols for account, symbol, position,
order and execution-history snapshots, and concrete execution primitives.
The existing `workspace.trading.Trading` composition satisfies `TradingRuntime`
directly. There is no parallel block implementation, compatibility facade, or
workspace-to-block forwarding helper. Include modules never import workspace.

Order blocks own scope filtering, best/worst selection, duplicate policy,
reversal, pending replacement and multi-target modification. Market/limit/stop
entries share one internal workflow; other reusable algorithms stay in their
owning packages' `_common.py` modules. StrategyControl blocks own position
predicates, aggregation, history selection and time-sensitive queries.
`strategy_control/history.py` contains shared lifecycle reconstruction and the
`ClosedTrade` record; WhatIf adapters consume that canonical record.

`workspace/trading/Trade` retains raw MQL-compatible calls plus:

- `prepare_entry_request`: normalize a concrete entry using instrument constraints
  and executor defaults.
- `send_checked`: broker request checking and submission.
- `close`: close one explicitly selected position snapshot and volume.
- `cancel`: cancel one explicitly selected pending-order snapshot.
- `modify_protection`: normalize and submit protection on one selected snapshot.
- `operation_lock`: serialize block workflows sharing the executor.

These primitives contain request construction, volume/grid/filling checks and
backend access, without deciding which strategy-owned orders should be affected.
Tick-grid normalization is shared once in `order/types.py`.

Lowercase helper methods have been removed from Trade, AccountProxy, PositionProxy,
OrderProxy and HistoryOrderProxy. `TradeFilter` and `ClosedTrade` are no longer
exported by workspace trading. All affected Python callers and exit scheduling
use the canonical block functions/contracts directly. Exit-policy scheduling
remains outside this migration's donor folders.

## Calling the blocks

```python
from app.include.blocks.order.open.enter_at_market import enter_at_market
from app.include.blocks.order.close.close_best_position import close_best_position
from app.include.blocks.order.types import TradeFilter
from app.include.blocks.strategy_control.market_positions_count import market_positions_count

await enter_at_market(trading, "EURUSD", 1, 0.02, magic=42)
scope = TradeFilter("EURUSD", magic=42)
count = await market_positions_count(trading, scope)
closed = await close_best_position(trading, scope)
```

Catalog descriptors can instantiate configured async callables. Calling such a
callable returns an awaitable; an execution runner must await it. Descriptor
construction validates configuration and performs no trading I/O. The registry
now resolves postponed annotations in the callable's defining namespace before
building its typed configuration model.

## Explicit semantics and donor differences

- Scope: `None` symbol/magic means any; zero magic is exactly zero. Direction is
  1/-1/0, comments match substrings, and optional tickets narrow selection.
  Resolve symbolic Current/Any and strategy identity at the caller/runner boundary.
  There is no strategy-name ownership field in current broker contracts.
- Best/worst: rank reported profit plus swap and commission, ties in backend
  collection order. Close operations affect positions; cancellation affects pending
  orders. Bulk actions stop on incomplete/failed results.
- Pending replacement: validate the new candidate before cancelling old orders,
  verify disappearance, then submit. Reversal verifies opposite positions closed
  before entering. These workflows are serialized per executor but not atomic
  across external terminals or independent executor instances; no automatic retry.
- Entry/protection inputs are evaluated sizes and absolute price levels. Formula
  evaluation, money-management selection, ATM multi-exit orchestration, platform
  export rules and bar-validity scheduling are not implemented by this migration.
  Pending expiry uses explicit aware datetimes; a strategy runner must translate
  chart bar validity using its market calendar.
- Protection preserves the other level and pending entry/expiration/filling.
  Stop-loss tightening is an optional strategy policy. Zero removes protection.
- MarketPosition uses the first matching position's direction; long and short
  predicates can both be true in hedged accounts. Size is gross summed volume.
- OrderOpenPrice / OrderSL / OrderPT share one implementation across positions
  and pending orders. Default selects positions first then pending orders;
  `pending=False` / `True` selects an explicit view. Missing values return -1.
- Open money P/L is net profit including available commission/swap. Optional
  decision-price mappings value positions without mutating backend state.
  Pip P/L uses explicit instrument pip size, falling back to tick size.
- Closed-trade queries reconstruct completed lifecycles from executions, correctly
  attributing partial closes, reversals, fees and opening identity. Cancelled orders
  do not become completed trades. Missing/ambiguous execution history raises.
- Bar counts require actual chart starts and explicit aware evaluation time;
  absent trades return -1. Recent-close predicates are stable and non-consuming,
  rather than copying donor engine-specific shortcuts and mutable scan cursors.

These are canonical Python counterparts using the application's explicit trading
contracts, not a claim of identical SQX platform/export behavior. The donor
snippets use SQX trader abstractions; the Python blocks similarly use an injected
runtime rather than broker transport or simulator fill implementation.

## Qualification

Tests cover donor manifest completeness and registry ownership for all 37 IDs,
async catalog instantiation/execution through an independent runtime, real
simulator catalog execution, configuration validation, absence of obsolete helper
methods, typed and dictionary backend responses, ranking, scope, protection,
partial closes, failed/unconfirmed workflows, concurrent entries, history
reconstruction and evaluation-time behavior. Existing WhatIf tests now import
ClosedTrade from its canonical owner.
