# Databank UI Plugin

`src/plugins/databank/` is the HaruQuantAI frontend presentation of the SQX
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

The splitter reproduces the observed donor mechanism: a three-state
collapsed/expanded/maximised lower pane, collapsed by default on load, with
the count bar ("DATABANKS {n} / STRATEGIES: {m}"), the centered chevron
cluster (maximise, drag-resize, collapse), a 100px expanded minimum, and a
window resize dispatch on every state change. Chevron-only toggle matches the
donor's observable behavior (its header click handler is dead code). Evidence:
`SQX144-EV-000025`, `SQX144-EV-000026`, `SQX144-EV-000027` in
`docs/dev/evidence/reimplementation.json`.

Displayed counts are fixture truth (currently 3 / 70), labelled demo. Panel
content, metrics, and actions are prototype presentation and make no SQX
metric or parity claim.

## Feature registry (this domain)

| Feature ID | Feature | Status |
|---|---|---|
| FEAT-UI-DATABANK_BUILDER | Shared databanks lower pane for project workspaces: SQX-parity three-state splitter (collapsed count bar, expanded split with drag-resize, maximised) with demo fixture data; panel content styling is prototype, not SQX parity | implemented (`ProjectDatabanks/DatabankSplitter.tsx`, `ProjectDatabanks/DatabankPanel.tsx`, mounted in `src/app/App.tsx` for builder/retester/optimizer/portfolio/projects) |

## Backend ownership gap

No backend databank feature is registered. Live record feeds, bank
persistence, views, and metric computation require an approved plan under the
future workspace/plugin architecture before any UI claim of authority.
