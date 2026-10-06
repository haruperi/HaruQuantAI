# HaruQuantAI UI

`app/ui/` is the retained React/TypeScript workstation prototype. It preserves
the product's visual language, workspace layouts, interaction experiments, and
test assets while the backend is rebuilt.

## Current truth

- The UI is mock-backed and uses frontend fixtures, Zustand stores, and browser
  storage for many simulated resources and jobs.
- Provider-specific Data Manager modules and hard-coded Builder/catalog metadata
  remain in the prototype.
- The Python host shell under `app/host/` is available as a candidate and the
  UI host can establish a session, signal readiness, and synchronize shell
  presentation preferences. Quantitative workspace backends are not yet
  implemented.
- Labels such as Backend, Database, workers, latency, jobs, exports, compilation,
  or trading are demonstrations unless explicitly driven by future gateway data.
- UI behavior is not authoritative evidence for quantitative, persistence,
  authorization, or external-integration semantics.

## Retained technology

- React and TypeScript
- Vite
- Zustand
- React Router
- TanStack Table/Virtual
- Dockview
- Lightweight Charts
- Vitest and Playwright

## Future boundary

The schema-driven UI architecture must separate:

1. **Catalog cache:** immutable backend plugin/workspace descriptions.
2. **Remote resource state:** server-owned datasets, strategies, runs, jobs, and
   artifacts accessed through a typed gateway.
3. **Draft state:** recoverable user edits that are not yet authoritative.
4. **View state:** tabs, filters, selection, panel layout, theme, and zoom.

Backend plugin additions must appear through a catalog snapshot and a bounded
generic renderer vocabulary. The UI must not maintain plugin-specific copies of
parameter schemas, optimizer bounds, output types, or execution logic.

Whole new interaction models may require a reviewed generic renderer or explicit
UI extension. Metadata is not assumed capable of safely producing arbitrary UX.

## Ratified workspace and wire boundary

[ARCHITECTURE.md](../../docs/ARCHITECTURE.md) owns the target; this README does
not claim that the retained prototype implements it.

- Backend workspaces live under `app/workspace/<Domain>/` and plugins under
  `app/plugins/<X>/`, paired with `app/ui/src/workspace/<Domain>/` and
  `app/ui/src/plugins/<X>/`. A workspace selects plugins through public
  contributions; it does not install them or own shared infrastructure.
- The host owns the shared transport envelope and startup catalog. Each
  workspace or plugin owns its public wire contract. The UI consumes typed
  JSON projections, not Python classes, factories, registry objects, or
  contexts. The concrete shared plugin metamodel has not yet been ratified.
- Generic controls will be bounded to declared forms, groups, typed ports,
  tables, and charts. A route string cannot supply new React behavior. Existing
  static routes and hard-coded catalogs require a separately approved migration.
- Graph editors display the same immutable versioned DAG used by execution,
  including stable node/port IDs and plugin versions. Comparisons are ordinary
  plugin nodes. User edits create revisions; the backend validates types, units,
  alignment, permissions, and compatibility before executing commands.
- Parameter validity, optimizer bounds, and parameter-derived warm-up come from
  plugin-owned schema/validation. The UI must not reconstruct numerical policies.
- Distinguish installed availability, workspace/profile enablement, and operation
  authorization. Missing optional capabilities disable their operation, not all
  editing. Unsupported exports must not appear as working targets.
- Two workspaces may select the same contribution. Removing one workspace does
  not remove shared children; missing nodes remain lossless placeholders. Unknown
  document versions may be retained read-only but cannot be executed or silently
  rewritten. Backend truth stays separate from cache, drafts, and view state.

## Development

```powershell
npm install --prefix app/ui
npm --prefix app/ui run dev
```

## Verification

```powershell
npm --prefix app/ui run typecheck
npm --prefix app/ui run test
npm --prefix app/ui run build
npm --prefix app/ui run test:ui
```

The Playwright suite requires its configured browser/runtime environment. Unit,
typecheck, and build qualification remain mandatory for source changes.

## Refactoring constraints

- Preserve accessibility, stable identity, and honest loading/error/unavailable
  states.
- Never move backend algorithms into the UI to keep a prototype working.
- Mock services implement the same future transport boundary and are selected at
  the UI composition root, not imported directly by production components.
- Browser storage is limited to preferences and explicitly recoverable drafts;
  it is not durable business truth.
- Unknown or removed algebra nodes are rendered as lossless unavailable
  placeholders rather than deleted or reinterpreted.
