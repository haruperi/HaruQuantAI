# Builder Workspace UI

`src/workspace/Builder/` is the HaruQuantAI frontend presentation of the SQX
Builder product: the strategy-building workspace with its Progress,
Full settings, and Results panels, and the shared databanks pane below.
It is UI-only in the current slice — demo fixture data, no build engine.

## What lives here

- `BuilderWorkspace.tsx` — the SQX-parity dashboard shell: the 51px header
  with the clickable project name and the Progress / Full settings / Results
  large tabs (Progress is the initial panel), plus the corrected Full settings form and the linked Results workspace.
- `ProgressDashboard.tsx` — the three-column Progress dashboard and the
  deterministic local mock runner (Start/Pause/Stop drive demo state only;
  no network calls are made from the Progress tab).
- `EnginePanel.tsx` — engine column: control card (Stop/Pause/Start, config
  dropdowns, fitness-evolution launcher), infinite progress bar, Task line,
  engine log with Clear log / Clear log on start / Memory cleanup, the Build
  stats table with Detailed popups, and the "No strategies generated?" link.
- `EngineCharts.tsx` — the two engine chart cards with the hover-border type
  select and hand-drawn demo SVG charts.
- `SettingsSummary.tsx` — Settings summary column: Use predefined config
  menu, Data rows, Build options rows (click opens Full settings), and the
  cross-check switch tree with Disable all.
- `ResultsColumn.tsx` — best-strategy result cards with the shared Sample
  selector; clicking a card opens the Results tab.
- `FitnessEvolutionModal.tsx` — the SQX-parity modal shell (`SqdModal`) and
  the Fitness evolution popup.
- `fixtures.ts` — demo data for the Progress tab (idle/running stats, chart
  series, settings summary values, cross checks, best strategies).

## Donor parity scope (SQX 144.2953)

The Progress tab parity slice covers (evidence `SQX144-EV-000032..037`):
dashboard header and large tabs; the 556px / 500px / flex three-column
layout; the engine column composition (controls, infinite progress, log
card, Build stats table with idle values `0`, `0 ms.`, `0 / 0.00 %`,
`0.00`, and N/A Detailed popups); the two engine chart cards with the two
observed types; the Settings summary column with the eight predefined
config entries and the FAST / SLOW / VERY SLOW cross-check tree; and the
results column with Best/2nd/3rd cards (only the best card visible at
default zoom, matching the donor) with the shared Sample selector.

Dark and light values follow the app theme (donor SkinDark vs donor default
skin) through the shared `--sqx-*` variables plus local `--sqd-*` variables.

Honest gaps: the engine chart type list is backend-fed in the donor — only
the two screenshot-observed types ship here. Charts are look-alike SVG
mocks, not chart ports. The idle cross-check display titles come from the
installed web module sources; three of them may differ server-side. Full settings and Results have their own UI prototype slices below; visual similarity does not establish complete donor parity. No engine, metric, or data equivalence is claimed.

## Feature registry (this domain)

| Feature ID | Feature | Status |
|---|---|---|
| FEAT-UI-BUILDER_PROGRESS_TAB | Builder Progress tab SQX parity: donor dashboard header and tabs, three-column dashboard (engine / settings summary / results), engine controls with mock runner, log card, Build stats table with Detailed popups, two engine chart cards, cross-check switch tree, and best-strategy result cards — all fixture-backed | implemented (`BuilderWorkspace.tsx`, `ProgressDashboard.tsx`, `EnginePanel.tsx`, `EngineCharts.tsx`, `SettingsSummary.tsx`, `ResultsColumn.tsx`, `FitnessEvolutionModal.tsx`, mounted for `/builder`) |

## Backend ownership gap

No backend builder/build-engine feature is registered. Live build
execution, engine channels, log feeds, and best-results streams require an
approved plan under the future workspace/plugin architecture before any UI
claim of authority.

## Full settings parity slice (SQX 144.2953)

The Full settings panel is the donor Advanced settings surface (evidence
`SQX144-EV-000039..043`, corrected by `SQX144-EV-000055..057`): the "Advanced settings" title, the 10-tab default Build strip (What to build, Genetic options, Data, Trading
options, Building blocks, ATM, Money management, Cross checks (robustness),
Ranking, Notes), with Parts to improve shown only for Improve existing strategy, per-tab description headers with
Help links opening the public donor docs, the lock overlay while the mock
engine runs, and direct tab navigation. The template contains prev/Close/next controls, but the inspected tab CSS hides that footer; the UI follows the supplied screenshot. Tab controls follow the donor
templates with defaults from the installed Build task template (genetic:
100 generations / 100 population / 4 islands; trading options; MM methods;
119-entry building block catalog). Deep editors (block parameter popups,
ATM formula editors, fitness formulas, per-check dialogs) are donor-style
fixture demos — labelled, no engine claims. The old prototype settings
page and its modals were removed as superseded.

| Feature ID | Feature | Status |
|---|---|---|
| FEAT-UI-BUILDER_FULLSETTINGS_TAB | Builder Full settings tab SQX parity: Advanced settings shell with conditional Build tabs, bounded cards, shared controls, additional-build-config gear popups and lock overlay — fixture-backed | implemented (`FullSettingsView.tsx`, `settings/*Tab.tsx`, `settings/SettingsControls.tsx`, `settings/settingsFixtures.ts`) |

## Results tab parity slice (SQX 144.2953)

The Results panel is the donor RESULTS overlay surface (evidence
`SQX144-EV-000045..000047`): the "No result chosen" info line, the
quant-tabs strip (Overview, SP overview, List of trades, Equity chart,
Trade analysis, Profile chart, Strategy config, Source Code) with the two
custom analysis tabs (Prop Monte Carlo, Prop analytics; green puzzle icon,
Rename/Delete menu) sorted last, the "+ New analysis" control with its
create-plugin modal, the fixed Reload link, and the shared Data /
Direction / Sample toolbar with per-tab extras (Template, View + manage
gear + Export + Include expired, X Axis + Benchmark + Subcharts settings,
Period by, source-code form with Parameter variables menu). Empty states
match the donor ("No strategy selected"). The donor's page-reload Reload
is adapted to a view-state reset. Backend-driven option lists (sample
percentage items, MM types, custom tab content) are labelled fixtures.
The shared `workspace/Results/ResultsWorkspace.tsx` prototype remains for
the Optimizer/Retester workspaces.

| Feature ID | Feature | Status |
|---|---|---|
| FEAT-UI-BUILDER_RESULTS_TAB | Builder Results tab SQX parity: info line, quant-tabs strip with custom analysis tabs and menus, + New analysis modal, Reload link, shared Data/Direction/Sample toolbar, per-tab chrome and empty states — fixture-backed | local UI prototype; populated flows implemented, complete SQX parity unverified (`ResultsView.tsx`, `results/*`) |

## Header and Full settings correction (2026-09-25)

The header, Advanced settings title and settings strip occupy separate layout
rows. The default title is Builder. Cards use bounded widths and filled theme
surfaces, with a narrow Help row, inline spinners and aligned gear rows. The
Results panel stays inside the panel host instead of covering the header.

Evidence SQX144-EV-000055..000057 corrects the historical default 12-tab and
visible-footer claims in record 000038. That historical record remains intact
and linked as superseded. Custom analysis is a separate task, not a Build tab.
Parts to improve is conditional. The footer conclusion is a bounded static-CSS
inference, pending inspection of the installed runtime cascade.

Local state survives settings-tab navigation. Gear Reset restores the selected
fixture setting; file selection displays the chosen name; Data presets update
local date ranges; genetic filters can be added/edited/removed; ATM offers a
fixture exit-method chooser; cross-check Save/Load stores a labelled in-memory
snapshot. None of these actions executes or persists a research configuration.
Selecting another top-level panel or remounting the workspace resets settings.

Verification includes browser screenshots of all ten default tabs, all six
additional-config dialogs, conditional visibility, keyboard tab activation,
local state retention, Data presets, genetic filters, ATM insertion, and
cross-check snapshot restoration. See the task walkthrough under
`.agents/logs/2026-09-25T145329_builder-settings-visual-correction/`.

Remaining limits: the supplied screenshot establishes only What to build's
visual target. Deep parameter/formula editors, engine-fed catalogs and custom
analysis contents remain partial fixtures. Screenshot configuration values can
differ from the installed-template fixture defaults retained here. No 100%
visual, runtime or quantitative parity is claimed. Backend/DB files are unchanged.

## Results populated UI correction (2026-09-25)

`FEAT-UI-BUILDER_RESULTS_TAB` now consumes the existing application selection at
BuilderWorkspace and passes a typed local result document to presentation tabs.
Databank double-click and ranked Progress cards activate Results. Trades, report
summaries, equity and drawdown are deterministic fixtures; filtering selects
precomputed snapshots, with no runtime backtesting or statistical engine.
The third fixture has no stored chart; the second enables Stockpicker log.

Implemented local interactions include trade direction/sample/market/expired
filters, ID/profit sorting, saved-column view create/edit/rename/delete, CSV
export, equity display controls, stored-chart zoom and navigation, profile path
selection/loading, mock source copy/download/refresh and custom-analysis tab
create/rename/delete. Results tab navigation preserves local view state; Reload
resets views. Leaving Results for another Builder panel remounts local state.
Static evidence additions are `SQX144-EV-000058..000064`.

Remaining parity gaps: populated report/chart layouts are independent mock
approximations, not pixel-diff-verified donor output. SP overview uses a bar chart
rather than the donor treemap. Optimization profile is not implemented. Advanced
correlation, robustness and distribution reports are simplified fixture panels.
XLSX export is explicitly unavailable; CSV works. Benchmark normalization and
chart unit choices retain UI selections but do not perform quantitative conversion.
Source generators produce labelled non-executable previews. Custom analyses remain
session-local previews. No backend algorithms, database schema or durable plugin
files were added. These limitations must not be described as 100% parity.

## Shared project presentation

The frame, modal shell, common settings and Results presentation now live in
`plugins/project/ProjectWorkbench` (FEAT-UI-PROJECT_WORKBENCH). Existing Builder
paths remain compatibility exports. Builder keeps Build-specific settings,
progress and fixtures. This extraction adds no Builder feature or parity claim;
existing limitations above still apply. Retester and Optimizer consume the shared
public entrypoint without importing Builder private components.
