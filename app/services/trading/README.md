# Trading Runtime Service

The trading runtime package is the broker-independent boundary for trading
requests, response envelopes, event contracts, public tool metadata, and
injected state/infrastructure ports.

## Boundary Role

This package owns platform-neutral trading contracts and persistence port
interfaces. It does not own broker SDK clients, concrete databases, secret
resolution, background schedulers, or live mutation policy storage. Concrete
implementations must be injected from infrastructure layers outside
`app/services/trading/`.

## Implemented Surface

- `contracts.py`: route/action enums, promotion and mutation capability enums,
  TIF and FIX execution states, request/response envelopes, quote snapshots,
  allocation vectors, regulatory tags, normalized broker result wrappers,
  order/position state projections, journal event contracts, and tool metadata.
- `state/ports.py`: injected protocols for `TradeStore`, `TradingStateStore`,
  `AuditSink`, `IdempotencyStore`, `EventJournal`, `Clock`, `RNG`, and
  `EncryptionProvider`.
- `tool_registry.py`: pure registry construction for AI-facing trading action
  drafts. The registry exposes no broker mutation tool.
- `__init__.py`: explicit public import gate with pure registry accessors.

## Inputs

Trading request contracts accept JSON-safe action payloads, route metadata,
promotion stage, mutation capability, optional allocation vectors, optional
regulatory tags, optional OCO/bracket linkage, and quote snapshots. Live
mutation requests require quote snapshots that match the requested symbol.

## Dependencies

The package depends on:

- `pydantic` for contract validation.
- `decimal.Decimal` for broker-critical numeric values.
- `app.utils.logger.logger` for operational logging.

The package must not import provider SDKs such as `MetaTrader5`, cTrader,
Binance, or broker-specific mutation clients.

## Determinism

Trading runtime code must use injected `Clock` and `RNG` ports for all time and
nondeterministic behavior. Direct calls to wall-clock or random APIs are
excluded from this package.

## Pending Runtime Areas

Actions, validations, execution coordination, gates, idempotency primitives,
reconciliation, monitoring, promotion, and MQL5-compatible read-only info
facades are intentionally pending and should be implemented in later
dependency-safe units.
