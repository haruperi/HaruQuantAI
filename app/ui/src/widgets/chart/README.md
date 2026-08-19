# Charting Tools Widget

`FEAT-UI-04` presents Data-owned historical bars, Indicators-owned overlays,
and non-authoritative drawing and appearance controls.

## Market-data lifecycle

- A symbol, timeframe, or range change first loads complete authoritative bars
  through `GET /api/v1/data/bars`.
- The initial/configuration load completes before a visible 10-second settling
  interval; only then does the widget demand one-second MT5 snapshots for its
  single active symbol.
- A same-timeframe-bucket Bid tick may update only the forming bar's High, Low,
  and Close. Open, volume, timestamp, and every prior bar remain authoritative.
- A timeframe boundary or newer-bucket tick aborts streaming and refreshes bars
  and selected indicators. Streaming remains closed while MT5 still returns the
  prior bucket; bounded delayed bar retries wait for the new authoritative bar.
  The widget never constructs a new candle from ticks.
- Unmounting or hiding the document releases live demand. Visibility recovery
  refreshes a missed boundary before streaming resumes.
- Historical Date ranges ending before today do not open a live subscription.

## Public API

`ChartWidget` is exported only through `index.ts`.

## Verification

`ChartWidget.test.tsx` covers historical loading, settling, one-symbol demand,
intrabar projection, canonical boundaries, delayed authoritative rollover,
connection-churn prevention, visibility, errors, indicators, controls,
drawings, gaps, and bounded rendering.
