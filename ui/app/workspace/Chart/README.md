# Chart workspace

Custom Canvas 2D chart at `/chart`, immediately below Data Manager in the sidebar.
It runs within the existing React 19 application. Prices, alerts and orders are
explicitly simulated; nothing connects to a broker or authoritative market feed.

## Run

From `ui`, run `npm install` then `npm run dev`, and open `/chart` on the
printed Vite URL. The initial view is XAUUSD / 3m / candles with a dark theme.
Chart theme and saved settings are independent of host settings.

## Controls

- Search 44 symbols by name or ticker, using arrow keys and Enter in search.
  Twelve intervals and seven price styles are available in the top toolbar.
- Drag the chart to pan; wheel or pinch to zoom around the pointer. Drag the
  price axis to scale; double-click/reset to restore automatic scale. Axis menus
  expose linear, logarithmic, percentage, indexed and reverse modes.
- Drawing groups provide 23 tools, including Fibonacci, pitchfork, Gann fan,
  shapes, annotations, brush and measurement. Use a click-drag for two anchors,
  staged clicks for three anchors, and double-click or Enter to finish polygons.
  Select objects to move their bodies or handles; use settings/context menus for
  style, lock, hide and delete. Magnet, persistent drawing mode, favorites and
  100-step undo/redo are supported. Locked drawings survive bulk deletion.
- Indicators: SMA, EMA, WMA, Bollinger Bands, VWAP, RSI, MACD, Stochastic, Volume
  and ATR. Parameters and presentation are configurable; oscillator panes have
  draggable sizing and manual axis scaling. Live calculations use checkpoints.
- Alerts support crossing up/down and entering/exiting channels, expiration and
  one-shot behavior. The alerts panel and toasts show simulated triggers.
- Paper market/limit orders support quantity and stop/target brackets. Positions
  show simulated P&L and can be closed. These are session-only, in quote-price
  units; there is no account balance, currency conversion or real execution.
- Replay selects a historical start, steps/plays at selectable speeds, hides
  future bars, and restores the live viewport on exit. Live order/alert price
  evaluation pauses during replay; alert expiration still follows wall time.
- Bottom controls provide ranges, clock zones, panels, fullscreen and PNG export.
  Export composites chart canvases and chart chrome. Settings include grid,
  crosshair, precision, session markers, gap display, volume, tooltip and minimap.
  Narrow toolbars scroll horizontally to retain access to their controls.

Press `?` for keyboard help. Common shortcuts: Alt+T/H/V/F/R for drawing tools,
T for text, M for magnet, Ctrl/Cmd+Z and Ctrl/Cmd+Shift+Z for undo/redo, Delete for
selection, Escape to cancel, +/- for zoom, 0 reset, L log, A auto, P crosshair,
/ search and F fullscreen. Shortcuts are scoped to the focused chart workspace.

## Data and persistence policies

`MockFeed` generates deterministic day-seeded stochastic OHLCV with trend and
volatility regimes and a forming-bar stream every 300 ms. It is a repeatable
simulation, not recorded historical prices. Forex/metals use UTC weekdays,
stocks use 13:30–20:00 UTC weekdays, and crypto runs continuously. Holiday and DST
exchange calendars are not modeled. Exchange clock means UTC for this feed.

Initial history spans 32 calendar days and expands for long ranges, bounded to
five years (`All` also uses that bound). Range buttons select a suitable interval:
1D uses 3m, 5D uses 15m, 1M uses 1h, and longer ranges use daily bars. Manual
interval selection remains available. Weeks start Monday UTC; months are calendar
months. Missing sessions produce no synthetic trading bars.

Local storage key `haruquantai.chart.v1` holds versioned chart preferences,
drawings by symbol/interval, indicator instances, favorites and alert definitions.
Writes are throttled. Invalid/future-version data is reported and preserved rather
than silently overwritten. Positions and undo history are not durable. Removing
the key intentionally resets saved chart state.

## Ownership

`src/engine` owns canvas rendering, transforms, input, animation and cleanup.
`src/feed` owns the mock adapter and resampling. Each `src/tools` implementation
owns its drawing geometry; each `src/indicators` implementation owns its local
calculation and parameters. `src/store` owns view state, history and persistence.
React components own controls/dialogs; quote readouts update outside React's
render cycle. No charting-library renderer or backend plugin contract is used.

## Verification

Run from the repository root:

```powershell
npm --prefix ui run typecheck
npm --prefix ui run lint:chart
npm --prefix ui run format:chart:check
npm --prefix ui run test
npm --prefix ui run build
uv run python scripts/ci_check.py
```

From `ui`, run `npm run test:ui -- tests/e2e/chart-platform.spec.ts
tests/e2e/chart-tools.spec.ts`, then run `npm run test:ui --
tests/e2e/chart-performance.spec.ts` separately for an isolated frame sample.
The performance harness measures about 5,000 visible candles during sustained
pan, with a one-second warmup and ten-second sample. Results depend on machine,
browser and display; they do not establish universal 60 FPS.

The implementation log at `.agents/logs/2026-09-25T180609_chart-platform/` contains
the approved plan, feature evidence matrix, screenshots and qualification results.
