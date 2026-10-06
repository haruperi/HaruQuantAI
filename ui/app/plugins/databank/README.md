# Databank UI Plugin

`app/plugins/databank/` is the HaruQuantAI frontend presentation of the SQX
ProjectDatabanks concept: the lower results panel embedded in Builder and the
other project workspaces. It is UI-only — fixture-backed demo data, no
backend databank capability exists yet.

## What lives here

- `fixtures.ts` — deterministic demo banks and strategies (three banks,
  seventy strategies). Values are demonstration data, not authoritative
  results.
- `ProjectDatabanks/DatabankSplitter.tsx` — the SQX-parity pane mechanism:
  collapsed count bar, expanded split, maximised state, drag-resize. Local
  view state only; not persisted (matches donor behavior).
- `ProjectDatabanks/DatabankPanel.tsx` and siblings — panel content (tabs,
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
| FEAT-UI-DATABANK_BUILDER | Shared databanks lower pane for project workspaces: SQX-parity three-state splitter and full panel content parity (toolbar with Save/Portfolio/Tools menu trees, tabs, Default - Main data grid, donor dialog set) with demo fixture data; engine/export actions are explicit deferred toasts | implemented (`ProjectDatabanks/DatabankSplitter.tsx`, `ProjectDatabanks/DatabankPanel.tsx`, `ProjectDatabanks/DatabankToolbar.tsx`, `ProjectDatabanks/DatabankDialogs.tsx`, mounted in `app/host/App.tsx` for builder/retester/optimizer/portfolio/projects) |

## Backend ownership gap

No backend databank feature is registered. Live record feeds, bank
persistence, views, and metric computation require an approved plan under the
future workspace/plugin architecture before any UI claim of authority.
