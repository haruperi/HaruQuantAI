# MT5 Market Ticks Diagnostic Widget

`FEAT-UI-25` provides a like-for-like diagnostic presentation of the tested
playground market-ticks table. It consumes HaruQuantAI's authenticated
`StreamEvent.v1` SSE boundary at the adopted `/api/v1/data/snapshot-stream`
route and renders source sequence, gaps, the served bid/ask wire values,
derived spread, broker time, age, and freshness.

D-UI feature shape (pipeline §4.8):

| Artifact | Responsibility |
| --- | --- |
| `manifest.ts` | Typed manifest: owning `FEAT-UI-25`, required `interfaces.observe-market-data@1`, optional `data.stream-market-events@1`, placement, dimensions, subscription, effects, accessibility, removal. |
| `config.ts` | Strict Zod configuration (symbols, freshness thresholds, reconnect bounds, persisted-state schema version); unknown fields throw. |
| `feature.tsx` | Lifecycle adapter: configuration lifecycle, subscription start/cancel/exact disposal, explicit availability response. |
| `MarketTicksTableWidget.tsx` | Focused presentation of served wire values only; renders no transport. |
| `useMarketSnapshots.ts` | Presentation-safe SSE consumption with reconnect, gap, and explicit unavailable (503) states. |
| `index.ts` | Deliberate public exports only. |

It owns presentation and reconnect state only. It does not connect directly to
MT5, define market-data truth, alter settings, or submit trading actions.
It aborts its snapshot stream while unmounted or while the browser document is
hidden, then reconnects when the document becomes visible. An absent gateway
(HTTP 503) renders the explicit `unavailable` state and recovers automatically
when the gateway returns; no prices are ever invented.

Verification: `MarketTicksTableWidget.test.tsx`,
`useMarketSnapshots.test.tsx`, `feature.test.tsx`, `manifest.test.ts`,
`config.test.ts`.
