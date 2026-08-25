# Manage Layouts (`FEAT-UI-MANAGE_LAYOUTS`)

Owning README: `app/ui/README.md` (§4.3). Feature slice for tabs, panels,
templates, persistence, and view scale.

## Implemented FRs (entry 1.3)

- `FR-UI-COMPOSE_PANELS` — engine docking interactions (1.01 foundation) plus
  this feature's versioned template contributions and the
  `workspace_templates` widget.
- `FR-UI-PERSIST_LAYOUTS` — `persistence.ts`: bounded localStorage snapshots
  scoped by actor/workspace/layout-schema-version, content-hashed by the
  serializer, never throws.
- `FR-UI-RESTORE_LAYOUTS` — schema-version-gated restore with deterministic
  diagnostics (`NO_PERSISTED_LAYOUT`, `SCHEMA_VERSION_MISMATCH`,
  `CORRUPT_SNAPSHOT`); missing widgets diagnosed by the engine serializer
  (`INCOMPATIBLE_WIDGET`).
- `FR-UI-MANAGE_TABS` — open/select/reorder via dockview; dirty-close guard
  wired in `WorkspaceHost` (panel close is vetoed for dirty panels until
  explicit resolution); bounded restoration via `max_restored_tabs`.
- `FR-UI-SCALE_VIEWS` — `ViewScaleProvider` + header `ScaleControls`
  (bounded zoom 0.75–1.5, fullscreen on the workspace outlet; header/status
  chrome never scales).

## State decision (migration plan §8.3)

Feature-local state uses React context only (`ViewScaleProvider`,
`ManageLayoutsClientProvider`, template request bus). No zustand; no
cross-feature or domain stores.

## Donor provenance

Templates are harvested from the V2 donor
(`.migration/v2-ui/src/widgets/workspaces/templates.ts`, guillotine
partition derived from its `dockLayout.ts`), converted V3-natively in
`templates.ts` — no donor module imports. Widget slugs follow donor domain
names; until later matrix rows register them, restoration diagnoses them
through the engine's missing-widget path (same convention as engine builtin
templates).

## Bounded dev usage evidence

Run `npm run dev` in `app/ui/` and open `/home`: header shows zoom/reset and
fullscreen controls; the Template select includes harvested presets (e.g.
`Chart + Ladder`); add widgets, mark state changes, close tabs (dirty tabs
prompt for explicit resolution); reload to observe persisted layout
restoration; clear site storage to observe deterministic defaults.
