# HSL execution capabilities

HSL JSON is the strategy definition. `app/core/trading/strategy/hsl` owns its
models, validation, compilation, and evaluator. Workspace imports remain compatible
aliases. A compiled plan embeds the complete canonical document and fingerprints
its registry dependencies. The ordinary `StrategyRuntime` executes that plan.
There is no Python expression node and no evaluation of source strings.

## Supported contract

| Area | Behavior and required evidence |
| --- | --- |
| Rules | Enabled flags, priority then ID order, exact event/symbol/timeframe filters, THEN and ELSE |
| Values | Typed literals, parameters, mutable variables, price fields, arithmetic, registered pure functions, causal registered indicators, selected output |
| State | Per-instance snapshots returned in effects; immediate ordered assignments; session variables reset by local date or explicit session-open event; revision changes require fresh state |
| Conditions | Numeric/string/bool comparisons, inclusive prior-sample crossings, logical/not, registered declarative recipes, owned-position and explicit session state, bounded observed temporal histories |
| Market data | Timestamped feeds per symbol/timeframe; only rows closed by event time are available; monotonic timestamps and explicit close timestamps for irregular calendars |
| Indicator inputs | Aligned, unshifted direct OHLCV series bindings; `source` aliases `close` for a close-only input; `main` aliases a descriptor's primary output |
| Entries | Market/stop/limit, absolute pending prices, action magic override, comments, expiry in fixed-duration bars |
| Protection | Per-action overrides or strategy defaults; pips/points/percent, actual requested ATR period, absolute expression/indicator prices, TP risk multiple |
| Sizing | Fixed quantity/cash, percent equity, stop-based risk percent; explicit instrument economics and account equity where needed; floor to volume step, reject below minimum |
| Management | Owned-symbol/magic close and partial close quantities, SL/TP changes, cancellations, time stop, breakeven, trailing distance, one-time partial exits |
| Policies | Local-time ranges/day/Friday exits; daily loss/drawdown; position limit and opposite-side filtering; daily cap using a host-confirmed filled-entry count |
| Historical host | One primary bar stream, start/stop and bar-open/bar-close events; additional feeds can supply as-of values; actual simulator trades, equity, commissions and slippage |
| Live host | Explicit event dispatch with supplied snapshots; submissions disabled by default; confirmed synchronous snapshots required; pending action/expiry and close side/quantity preserved; async and modify/cancel effects rejected until a qualified adapter is provided |
| Generation | `generate_hsl_strategy` produces validated canonical HSL and respects registry causal/generation-eligible metadata; research builder uses it; fresh libraries discover canonical owners, recipes, and comparisons together |
| Optimization | Project parameter/sizing changes rebuild canonical HSL and recompile, rather than editing a stale inventory |
| Export | Python delegates to the same runtime; HSL JSON preserves the document; pseudocode displays the complete definition |
| Storage | Host-owned integrity-checked atomic JSON records, cross-process exclusive locks, optimistic revisions, restart recovery; no SQL or automatic live restart |

The caller retains `effects.state_updates` for the next event. Supply a fresh state
for each strategy instance/revision. Effects describe intentions, not confirmed
broker fills. Hosts own dispatching confirmed execution lifecycle events. Temporal
conditions count observed bar events, not calendar gaps. Tick crossings require
closed-bar expression history; there is no invented prior quote snapshot.

Instrument economics specify pip/tick sizes, pip value per lot, contract size,
quantity bounds and quantity step. Historical PnL uses the configured simulation
`point_value`; callers must keep it consistent with the selected instrument.
Trailing `fixed_pips` converts the distance; `expression` and `atr` accept an
explicit distance expression in price units (an ATR node can supply that distance).
Pending orders reserve capacity without being counted as filled trades.
Daily trade limits require `context.entries_today`; the historical host counts
actual filled tickets, including closed and partially closed positions.
Session state must be supplied explicitly when a rule reads `session.is_open`.

## Explicitly unavailable

These are rejected, not implemented by approximation:

- Dynamic/portfolio universe selection and asynchronous multi-stream historical
  event orchestration. Reference feeds do not create additional trading events.
- Tick/timer/order/position/session lifecycle rules in the bar-only backtest host.
  The shared evaluator accepts exact explicit lifecycle events from a capable host.
- Prior mutable-variable/position history in crossing expressions without explicit
  history snapshots. Temporal conditions retain observed booleans instead.
- Non-causal indicators, unknown outputs/ports, shifted or arbitrary expression
  indicator input series, and unaligned input series.
- Legacy genetic crossover/mutation applied to canonical HSL plans. The legacy
  generator/genetic API remains available for older core documents.
- MQL4, MQL5, EasyLanguage, NinjaTrader, JForex and cTrader HSL exports. Legacy
  non-HSL export paths remain separate; rendering a template is not qualification.
- Retest adapters without actual evidence. Additional markets, higher precision,
  sequential optimization and walk-forward matrices require complete supplied
  run results/evaluators. SPP and walk-forward optimization are disabled because
  their current profit-only inputs cannot substantiate all advertised metrics.
  Monte Carlo retests run actual compiled strategies over perturbed bars.
- Backtests without explicit bars and persistence without a configured host store.

## Storage operation

Pass `HostStrategyStorage(directory)` to workspace services or set
`HARU_STRATEGY_STORAGE_DIR` to a dedicated host-owned directory. No directory is
chosen implicitly. File saves accept `expected_revision` for stale-editor
protection. Locks left after a process crash fail with `HSL_STORAGE_BUSY` and
require operator inspection; they are never silently removed. Integrity failures
fail closed. Restore does not start strategies or submit broker transactions.

## Standardization gate

This matrix defines executable boundaries; it is not a strategy authoring template.
The strategy template must remain unenforced until the owner reviews the completed
verification and explicitly accepts these supported and unavailable capabilities.
