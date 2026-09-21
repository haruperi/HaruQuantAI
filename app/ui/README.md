# HaruQuantAI UI

`app/ui/` is the retained React/TypeScript workstation prototype. It preserves
the product's visual language, workspace layouts, interaction experiments, and
test assets while the backend is rebuilt.

## Current truth

- The UI is mock-backed and uses frontend fixtures, Zustand stores, and browser
  storage for many simulated resources and jobs.
- Provider-specific Data Manager modules and hard-coded Builder/catalog metadata
  remain in the prototype.
- There is no active Python gateway or production backend.
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
