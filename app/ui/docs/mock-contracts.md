# Mock service contracts

`ResearchService` is the boundary used by project controls. It exposes asynchronous `start`, `createCandidates`, `retest`, and `exportStrategy` operations. A future backend can implement the same interface without changing the presentation components.

Stable records are defined for datasets, instruments, strategy revisions, trades, equity points, databanks, jobs, optimization settings, portfolios, rules and workflow tasks. Selection stores stable IDs. Seeded fixtures generate every trade, equity point and headline metric from one deterministic record:

- starting balance is 100,000;
- realized P/L changes balance at trade exit;
- equity points are derived from cumulative realized P/L;
- drawdown is peak balance minus current balance;
- net profit equals ending balance minus starting balance;
- trade count equals the trade list length;
- profit factor equals gross wins divided by absolute gross losses.

Portfolio equity replays member equity deltas against shared starting capital, scaled by enabled member weights. Optimization trials are deterministic projections around the selected strategy metric and retain explicit parameter values. Robustness verdicts show their acceptance rule and scenario count.

Persistence currently uses a Zustand JSON envelope in `localStorage` under schema key `sqx-recreation-v1`, version 1. This is appropriate for the demonstration size; a backend implementation should move substantial strategies/trades/artifacts to IndexedDB or server storage and retain a migration registry. Corrupt envelopes fall back to seeded fixtures through the persistence middleware's initial state.

Interrupted jobs remain in their last persisted state. They are not silently completed on reload. Users can resume, stop, or reset them. Provider, compiler, remote, SMTP, broker and external-script operations are configuration-only simulations and never transmit data.
