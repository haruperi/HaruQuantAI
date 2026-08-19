# MT5 Market Ticks Diagnostic Widget

`FEAT-UI-25` provides a like-for-like diagnostic presentation of the tested
playground market-ticks table. It reads the non-secret configured symbol list,
consumes HaruQuantAI's authenticated `StreamEvent.v1` SSE boundary, and renders
source sequence, gaps, quote values, broker time, age, and freshness.

It owns presentation and reconnect state only. It does not connect directly to
MT5, define market-data truth, alter settings, or submit trading actions.
It aborts its snapshot stream while unmounted or while the browser document is
hidden, then reconnects when the document becomes visible.

Verification: `MarketTicksTableWidget.test.tsx`, `useMarketSnapshots.test.tsx`.
