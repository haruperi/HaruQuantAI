# Databank UI Plugin

`app/plugins/databank/` is the HaruQuantAI frontend presentation of the SQX
ProjectDatabanks concept: the lower results panel embedded in Builder and the
other project workspaces. It is UI-only — fixture-backed demo data, no
backend databank capability exists yet.

## What lives here

- `fixtures.ts` — deterministic demo banks and strategies (three banks,
  seventy strategies). Values are demonstration data, not authoritative
  results.
- `ProjectDatabanks/views/databanks.tsx` — the SQX-parity pane mechanism:
  collapsed count bar, expanded split, maximised state, drag-resize. Local
  view state only; not persisted (matches donor behavior).
- `ProjectDatabanks/views/databank.tsx` and siblings — panel content (tabs,
  toolbar, table, dialogs) in its current prototype styling; SQX content
  parity is a separate upcoming feature.

## Donor parity scope (SQX 144.2953)

Two slices own the parity claim:

1. **Splitter mechanism** (`DatabankSplitter.tsx`): three-state
   collapsed/expanded/maximised lower pane, collapsed by default, count bar
   ("DATABANKS {n} / STRATEGIES: {m}"), centered chevron cluster,
   drag-resize, 100px expanded minimum, window-resize dispatch on change.
   Chevron-only toggle matches the donor's observable behavior (its header
   click handler is dead code). Evidence: `SQX144-EV-000025..027`.
2. **Panel content** (this slice): donor toolbar inventory with Save /
   Portfolio / Tools menu trees (including nested Edit and Select
   submenus), centered Records counter, right-side refresh + View combo +
   gear, light quant-tabs bank strip without counts/add-button (Builder
   product), "Default - Main data" grid columns with (IS) suffixes, and
   the donor dialog set (Load, Retest, Save, Rename, Delete/Clear
   confirms, Set note, Manage Views, Filter by correlation, Compare) with
   verbatim texts. Mock flows are truthful: row operations act on fixture
   data; engine/export operations show explicit deferred toasts. Evidence:
   `SQX144-EV-000028..031`.

Displayed counts and metrics are fixture truth (currently 3 banks / 70
strategies), labelled demo. No SQX metric or engine parity is claimed.

## Feature registry (this domain)

| Feature ID | Feature | Status |
|---|---|---|
| FEAT-UI-DATABANK_BUILDER | Shared databanks lower pane for project workspaces: SQX-parity three-state splitter and full panel content parity (toolbar with Save/Portfolio/Tools menu trees, tabs, Default - Main data grid, donor dialog set) with demo fixture data; engine/export actions are explicit deferred toasts | implemented (`ProjectDatabanks/views/databanks.tsx`, `ProjectDatabanks/views/databank.tsx`, `ProjectDatabanks/DatabankToolbar.tsx`, `ProjectDatabanks/DatabankDialogs.tsx`, mounted in `app/host/App.tsx` for builder/retester/optimizer/portfolio/projects) |

## Backend ownership gap

No backend databank feature is registered. Live record feeds, bank
persistence, views, and metric computation require an approved plan under the
future workspace/plugin architecture before any UI claim of authority.

## Structural ownership qualification (2026-10-06)

The earlier parity statements and SQX144-EV references above are historical claims;
this structural cleanup does not independently establish or renew them. Canonical
reimplementation ledger/schema were not found. No behavioral parity is asserted
by the new source manifest.

FEAT-UI-DATABANK_BUILDER retains ownership of this frontend pane. Its mapped entry
is ProjectDatabanks/module.ts; views/databanks.tsx composes the splitter and
views/databank.tsx presents the bank. Controllers own existing state/lifecycle and
DatabankService.ts attaches existing stores. Status: structural cohort implemented;
verification and limits recorded in the cohort walkthrough.

- FR-UI-DATABANK-source-mapping: exact ProjectDatabanks paths/casing/provenance.
- FR-UI-DATABANK-workflow-preservation: preserve fixture pane and mock operations.
- FR-UI-DATABANK-clean-room: independent target code; no donor backend copying.

DEC-UI-DATABANK-STRUCTURAL-OWNERSHIP: map
SQX_REFERENCE_ROOT/internal/plugins/ProjectDatabanks to
HARUQUANTAI_ROOT/ui/app/plugins/databank/ProjectDatabanks. Shared actions, view
management, rename, correlation and compare remain retained target dependencies
until their own bounded donor cohorts. Shared CSS remains a host dependency;
pane-specific stylesheet is mapped. Existing view persistence and mock fixtures
remain unchanged. No quantitative service or backend databank is introduced.

## ResultsDatabankViews structural ownership (2026-10-06)

DEC-UI-DATABANK-VIEWS-STRUCTURAL-OWNERSHIP: map
SQX_REFERENCE_ROOT/internal/plugins/ResultsDatabankViews to
HARUQUANTAI_ROOT/ui/app/plugins/databank/ResultsDatabankViews.
FEAT-UI-DATABANK_BUILDER owns this existing frontend view editor;
FR-UI-DATABANK-source-mapping also covers this plugin, with the existing
FR-UI-DATABANK-workflow-preservation and FR-UI-DATABANK-clean-room requirements.
Status: structurally relocated; qualification and limits recorded in its walkthrough.

module.ts exports ManageViewsDialog from databankViews.tsx. DatabankViewsCtrl.ts
owns existing editing state; DatabankViewsService.ts attaches the existing
ProjectDatabanks/databankStore.ts authority. ProjectDatabanks/databankColumns.ts
remains shared by metrics, table and editor; toolbar view selection stays in the
pane. The target view composes independently authored editor presentation where
the donor HTML delegates to internal/web/app/directives/manageViewsDialog.
That shared donor directive is outside this plugin inventory; matching this
wrapper does not claim shared-directive or advanced settings parity. The JAR is
excluded backend scope. No XML requests, new persistence, metric formulas or
backend functionality were introduced. Historical parity claims remain qualified.

## DatabankRename structural ownership (2026-10-06)

DEC-UI-DATABANK-RENAME-STRUCTURAL-OWNERSHIP maps
SQX_REFERENCE_ROOT/internal/plugins/DatabankRename to
HARUQUANTAI_ROOT/ui/app/plugins/databank/DatabankRename, preserving ui/ nesting.
FEAT-UI-DATABANK_BUILDER owns this existing frontend responsibility under
FR-UI-DATABANK-source-mapping, FR-UI-DATABANK-workflow-preservation and
FR-UI-DATABANK-clean-room. Status: structurally extracted; verification and
limitations recorded in its walkthrough.

ui/module.ts exports RenameStrategiesDialog; ui/databankRenamePopup.tsx owns its
presentation and ui/DatabankRenamePopupCtrl.ts owns input state/confirmation.
Existing ProjectDatabanks/DatabankDialogs.tsx retains shared SqxModal/SqxButton
and sibling dialogs. Toolbar registration, selection guard and host mock rename
callback remain existing pane dependencies. Backend/project artifacts are
excluded. The donor running/loading guard and backend rename progress/request
are not qualified or added here. Shared modal focus restoration/trapping remains
unqualified. Matching structure does not establish runtime or algorithm parity.
