# Builder Workspace UI

`src/workspace/Builder/` is the HaruQuantAI frontend presentation of the SQX
Builder product: the strategy-building workspace with its Progress,
Full settings, and Results panels, and the shared databanks pane below.
It is UI-only in the current slice — demo fixture data, no build engine.

## What lives here

- `BuilderWorkspace.tsx` — the SQX-parity dashboard shell: the 51px header
  with the clickable project name and the Progress / Full settings / Results
  large tabs (Progress is the initial panel), plus the current Full settings
  form (prototype styling) and the linked Results workspace.
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
installed web module sources; three of them may differ server-side. The
Full settings and Results tab contents are our prototype surfaces, not yet
donor-parity. No engine, metric, or data equivalence is claimed.

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
`SQX144-EV-000038..043`): the "Advanced settings" title, the 12-tab Build
strip (What to build, Parts to improve, Genetic options, Data, Trading
options, Building blocks, ATM, Money management, Custom analysis, Cross
checks (robustness), Ranking, Notes), per-tab description headers with
Help links opening the public donor docs, the lock overlay while the mock
engine runs, and prev/Close/next navigation. Tab controls follow the donor
templates with defaults from the installed Build task template (genetic:
100 generations / 100 population / 4 islands; trading options; MM methods;
119-entry building block catalog). Deep editors (block parameter popups,
ATM formula editors, fitness formulas, per-check dialogs) are donor-style
fixture demos — labelled, no engine claims. The old prototype settings
page and its modals were removed as superseded.

| Feature ID | Feature | Status |
|---|---|---|
| FEAT-UI-BUILDER_FULLSETTINGS_TAB | Builder Full settings tab SQX parity: Advanced settings shell with the 12 Build tabs, shared donor-look controls, additional-build-config gear popups, lock overlay, and prev/Close/next — fixture-backed | implemented (`FullSettingsView.tsx`, `settings/*Tab.tsx`, `settings/SettingsControls.tsx`, `settings/settingsFixtures.ts`) |
