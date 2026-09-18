# Parity and verification ledger

## Completed and exercised

- Dense shell, application switching, dark/light skin, settings with draft/cancel/save, notifications and versioned persistence.
- Project header, progress lifecycle, coherent deterministic logs/counters, settings, linked results and lower databank.
- TanStack sorting and row identity plus TanStack Virtual scrolling for seeded strategy banks.
- Copy/move semantics, rename/notes, delete confirmation, filtering and selection.
- Dockview-hosted result panel and Lightweight Charts equity/drawdown views with resize cleanup.
- Builder/Improver settings, Optimizer modes, and the Data Manager source controls: Dukascopy, TickDownloader, File import, SQ Equity, SQ Futures, Darwinex, Crypto, Yahoo, and MetaTrader 5 menus; Crypto exchange choices; provider-specific dialogs; and Update all, Update selected, Mass delete, Save, and Load actions. Also completed are AlgoWizard rule edits, portfolio weights/results, workflow tasks, and extension surfaces.
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

The application should therefore be described as a broad, coherent frontend recreation and research simulator—not full numerical or pixel parity with the proprietary reference.
