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
- `state/idempotency.py`: canonical SHA-256 idempotency material hashing,
  durable JSONL leases, duplicate rejection, completed-envelope caching, and
  reconciliation-required expiry handling.
- `state/event_journal.py`: encrypted append-only event journal with hash-chain
  records, logical sequence IDs, reconciliation scans, snapshots, replay
  reconstruction, retention seal events, and detached signatures.
- `state/manager.py`: local state update coordinator that persists snapshots and
  journals state-update events through injected stores.
- `tool_registry.py`: pure registry construction for AI-facing trading action
  drafts. The registry exposes no broker mutation tool.
- `config/`: immutable route, timeout, rate-limit, secret-reference,
  notification, credential-rotation, and broker security profile contracts.
- `security/`: public trading exception mapping, recursive redaction
  boundaries, and write-ahead dead-letter queue helpers for failed critical
  broker or audit events.
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

## Configuration And Security

Runtime configuration stores only secret references, never raw secret values.
Live mutation is disabled by default and resolves to `packaged_only` behavior
until policy enables mutation. Configuration reloads are validated through the
loader, versioned with a redacted hash, and immutable live-session keys are
blocked while a session is running.

Security boundaries map raw SDK, network, validation, permission, and
persistence exceptions into standard public error codes with request and
correlation IDs. Exported logs, alerts, events, reports, and chat payloads pass
through recursive redaction. Failed critical broker or audit payloads are
written to a redacted JSONL dead-letter log before recovery, and retry
thresholds relocate poison-pill events to manual review.

## Persistence

Idempotency records are derived from canonical JSON command material and stored
as durable leases. Active duplicates are rejected, completed duplicates return
their cached envelopes, and expired live leases transition to reconciliation
instead of retrying automatically.

Journal records are append-only encrypted JSONL entries with logical sequence
IDs and hash-chain links. Snapshots and replay helpers rebuild projections for
recovery or forensic reconstruction, while segment seals and detached
signatures support tamper-evidence checks.

## Pending Runtime Areas

Actions, validations, execution coordination, gates, idempotency primitives,
reconciliation, monitoring, promotion, and MQL5-compatible read-only info
facades are intentionally pending and should be implemented in later
dependency-safe units.
