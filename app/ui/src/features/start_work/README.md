# Start Work (`FEAT-UI-START_WORK`)

Owning README: `app/ui/README.md` (§4.2). This folder is the feature-slice
implementation for the start-work surface.

## Implemented FRs

- `FR-UI-PRESENT_HOME` — Home landing widget (`src/widgets/home/`):
  product/workspace identity, versions, and capability-aware entry points
  derived exclusively from the shell snapshot's capability-filtered
  workspace list.
- `FR-UI-SHOW_PRODUCT_NEWS` — Product news widget
  (`src/widgets/product_news/`): optional news in a dedicated region;
  offline/failed/empty news degrades only that widget region.

`FR-UI-RESUME_RECENT_WORK` and `FR-UI-LAUNCH_SHORTCUTS` are mock-build only
(Stage 14 de-mock gate 14.8); no completable implementation exists here.

## Bounded dev usage evidence

Run the Vite dev server from `app/ui/` (`npm run dev`) and open `/home`.
The dev composition root (`src/main.tsx`) injects the dev-only
`MockUiPresentationProvider`; mock-derived content is visibly labeled
non-authoritative in both widgets. NEWS fetch failures render a
non-blocking unavailable state inside the news widget only.
