# StrategyQuant X reference audit

Audit date: 2026-09-18
Reference installation: `SQX_REFERENCE_ROOT` (treated as read-only)

## Evidence reviewed

The implementation is based on a static crawl of the installed application, the supplied domain map, evidence index, structured JSON inventory, saved project archives, and representative web registrations/templates/controllers. The audited web roots include `app`, `common`, `BUILDER`, `RETESTER`, `OPTIMIZER`, `RESULTS`, `RESULTS2`, `SQMANAGER`, `TASKMANAGER`, `PORTFOLIOMASTER`, `PORTFOLIOCOMPOSER`, `AlgoWizard`, `SQEDITOR`, `SQXBUSINESS`, `SQXHOME`, and `HOME`. Plugin registrations, extension snippets, code templates, languages, saved projects, settings, and user result plugins were also sampled.

The supplied research inventory records 193 plugin directories, 280 plugin HTML views, 930 Java snippets, 3,180 code templates, and 15 saved project archives containing 90 workflow task entries. Those counts describe the reference, not a claim that this recreation reimplements every native engine or every source snippet.

Representative sources used directly:

- `internal/web/app/layout/views/header.html` — global settings, language, skin, zoom, help, about, update, reload and exit entry points.
- `internal/web/BUILDER/layout/views/layout.html`, plus equivalent Retester, Optimizer, Portfolio Master and Task Manager layouts — dashboard above a shared databank.
- `internal/web/SQMANAGER/layout/views/layout.html` — ribbon groups, batch progress, data tabs and no-data state.
- `internal/plugins/DataSourceDukascopy`, `DataSourceTD`, `DataSourceFiles`, `DataSourceSQEquityData`, `DataSourceSQFuturesData`, `DataSourceDarwinex`, `DataSourceCrypto`, `DataSourceYahoo`, and `DataSourceMt5Api` — provider registrations, menu commands, and the narrow dialog/controller artifacts needed to define the Data sources command surface.
- `internal/plugins/ProjectDatabanks/views/databanks.html` — cross-module databank placement.
- `internal/plugins/SettingsWhatToBuild`, `SettingsGeneticOptions`, `SettingsBlocks`, `SettingsOptimization`, `SettingsCrossChecks`, `SettingsRankings`, and `SettingsAdvancedTM` — project settings.
- `internal/plugins/Results*` and `internal/extend/Snippets/SQ/{Columns,Stats,TradeAnalysis,MonteCarlo}` — results and measures.
- `internal/web/AlgoWizard` and representative `.sqx` rule trees — authoring structure.
- Saved `user/projects/*/project.cfx` archives — workflow order and task applicability.

## Visual verification limitation

The installed executable was launched, but the environment's desktop-control bridge returned no native application windows. No reference state was edited. Layout, colors, density, and hierarchy therefore reconstruct the installed HTML/CSS/static resources; they are not claimed as screenshot-verified pixel parity. The frontend itself was inspected at a consistent desktop viewport after build.

## Inclusion register

Included as functional frontend simulations: application shell, Builder, Improver, Retester, Optimizer, Data Manager, databanks, linked Results, AlgoWizard, Portfolio Master, Portfolio Composer, Custom Projects, Code Editor, SQX Business surfaces, Prop analytics/result-extension identities, global settings, themes, persistence, fixture reset, file-import flow, mock source export, and deterministic job states. The Data Manager source surface names every supported provider and operation explicitly; it is a HaruQuantAI requirement derived from narrow behavioral evidence, not a claim of copied implementation or runtime parity.

Included as identifiable configuration surfaces rather than real host integration: provider connections, remote access, MCP, SMTP, external scripts, native compilation, broker/platform export, and worker nodes. These controls save or display mock state and state plainly that no external side effect occurs.

Excluded from parity claims: native backtest/genetic execution, proprietary SQX archive compatibility, actual provider downloads, real broker connections, remote worker discovery, native Java compilation, native Electron window behavior, license/update/payment flows, and numerical equivalence to SQX. Bundled libraries, obsolete/dev-only test pages, payment iframes, and shell-only Neural Network artifacts are not exposed as complete products.

## Technology

React 19, TypeScript 5.9 strict mode, Vite 7, Tailwind CSS 4, Dockview 4, TanStack Table 8, TanStack Virtual 3, Lightweight Charts 5, Zustand 5, Vitest 3, and Playwright 1.55. Exact resolved versions are in `package-lock.json`.
