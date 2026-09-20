# Parity and verification ledger

## Completed and exercised

- Dense shell, application switching, persistent labelled/icon-only sidebar modes, dark/light skin through Settings, notifications, versioned persistence, and the audited SQX Settings command hierarchy. The cleaned top action row includes Notifications, Debug Console, Grid Control, Volume & Market Profile, and Settings; redundant Theme/Help shortcuts, the development Feature Profile selector, and the duplicate Code Editor top action are omitted. Configuration has all seven active tabs; Benchmark, Remote access, MCP, SMTP, language, skin, zoom/fullscreen, links, license, About, reload, and Exit have browser-safe stateful behavior.
- Project header, progress lifecycle, coherent deterministic logs/counters, settings, linked results and lower databank.
- TanStack sorting and row identity plus TanStack Virtual scrolling for seeded strategy banks.
- Copy/move semantics, rename/notes, delete confirmation, filtering and selection.
- Dockview-hosted result panel and Lightweight Charts equity/drawdown views with resize cleanup.
- Builder settings, including improve-existing mode, Optimizer modes, and the Data Manager source controls: Dukascopy, TickDownloader, File import, Equity, Futures, Darwinex, Crypto, Yahoo, and MetaTrader 5 menus; Crypto exchange choices; provider-specific dialogs; and Update all, Update selected, Mass delete, Save, and Load actions. Also completed are AlgoWizard rule edits, portfolio weights/results, workflow tasks, and extension surfaces.
- Automated Data Manager coverage opens every provider command and Crypto exchange choice, exercises all five contextual actions, checks selection gating and the delete dependency warning, and rejects any provider-domain request during the scenario.
- Strict typecheck and production build.

## Partial parity / precise gaps

- Visual reconstruction is based on installed static resources; native screenshots were unavailable. Pixel parity is unverified.
- Retester shares the common settings frame; it does not yet expose every reference-only precision/additional-market control as a dedicated subsection.
- Several result extensions use coherent generic optimization/robustness projections rather than reproducing every specialized chart renderer (for example 3D surfaces and full correlation heatmaps).
- Import UI exposes explicit CSV/TSV parsing, column-mapping, timezone, timeframe, timestamp, error-handling, and batch-policy controls, but the current slice simulates validation and queuing rather than parsing or mutating real datasets.
- Source download is illustrative and not compiled. Proprietary `.sqx`/`.cfx` compatibility is not claimed.
- Layout persistence covers application state; Dockview geometry is not separately serialized yet.
- Visual comparison baselines and native-reference runtime comparison remain outstanding; the focused Playwright scenario verifies the complete Data sources command surface but does not establish pixel parity.
- Native execution, providers, external scripts, remote access, MCP, SMTP, license/update flows and live trading remain safe mock-only boundaries.
- Debug Console derives bounded messages from frontend jobs/notifications instead of the SQX websocket. Grid Control derives rows from mock jobs and deterministic finished fixtures instead of `gridControl/getData`; its three-second refresh updates the view timestamp without polling a backend. Volume Profile licensing and purchase remain informational links only.

The application should therefore be described as a broad, coherent frontend recreation and research simulator—not full numerical or pixel parity with the proprietary reference.
