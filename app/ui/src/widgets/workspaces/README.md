# Workspaces (`FEAT-UI-COMPOSE_WORKSPACE`)

## Purpose

Own `ui.workspace-layout@1`: the typed lazy widget registry, presentation-only
workspace state, templates, Dockview topology, unavailable-panel recovery, and
scoped observer cleanup. Domain jobs and business records remain owner-controlled.

## Public API

- `listWidgetRegistrations`, `getWidgetRegistration`, `registerWidget`, and
  `withdrawWidget` expose the single contribution registry. Exact disposers are
  idempotent and restore only the registration they withdrew or replaced.
  Component availability is separate from acceptance: legacy manifest/feature
  IDs and later planned owners are explicitly `UNQUALIFIED` until their own
  feature Tasks are independently accepted. Where a legacy manifest exists,
  its real capability/effect declarations are exposed instead of synthesized
  empty values.
- `useWorkspaceStore` owns presentation state. Only `workspaces`,
  `activeWorkspaceId`, and `defaultWorkspaceId` persist.
- `sanitizeDockLayout` and `recoverPersistedLayout` reconstruct a bounded
  allowlisted Dockview topology, strip arbitrary params/provider data, reject
  popouts and invalid geometry, keep valid siblings, and retain unknown widget
  types as explicit unavailable panels. Contradictory optional minimum/maximum
  constraints are omitted; floating groups with negative or over-limit anchors
  are dropped instead of being restored off-window.
- `WORKSPACE_TEMPLATES`, `findWorkspaceTemplate`, and `buildDockLayout` create
  Blank, Research, and existing workspace layouts from registered types only.
- `WorkspaceLayoutFeature` validates the schema-version-4 layout configuration;
  `allowCrossWindowPopout` is fixed to `false` because cross-window tear-off is
  not supported. Docking, tabs, splits, in-workspace floating, resizing, and
  keyboard repositioning remain supported. Layout saves use an internal 250 ms
  debounce; it is not public configuration.

## Interactive Usage

1. `FR-TRC-UI-COMPOSE_WORKSPACE-001`: open the Sidebar and add a registered widget. Sidebar,
   type validation, templates, and rendering resolve the same registry entry.
2. `FR-TRC-UI-COMPOSE_WORKSPACE-002`: save and reopen a Research workspace. A malformed or
   removed panel becomes unavailable without removing valid siblings; secret,
   strategy, raw-row, provider, and request objects are not persisted.
3. `FR-TRC-UI-COMPOSE_WORKSPACE-003`: select Research or another template, then dock, tab,
   split, float, resize, and move panels with Alt+Arrow. Focus remains within
   the workspace; cross-window popout is reported as unavailable.
4. `FR-TRC-UI-COMPOSE_WORKSPACE-004`: close an observing panel. Its scoped disposer releases
   browser effects, but no accepted owner job is cancelled. Use the owning job
   control when cancellation is intended.

Run the bounded offline companion:

```powershell
npm --prefix app/ui run usage -- src/widgets/workspaces/_usage.tsx
```

Expected output states that 26 contributions were discovered, the Research
layout was built, an unavailable panel was isolated, and observer disposal did
not cancel owner work. It requires no credentials, network, or live action.

## Verification

- `__tests__/traceability.test.tsx`: `AT-UI-COMPOSE_WORKSPACE-001` through `AT-UI-COMPOSE_WORKSPACE-004`.
- `__tests__/lifecycle.test.tsx`: `ATN-UI-COMPOSE_WORKSPACE-001`, including 100 registry
  enable/disable cycles, generation-stable lazy components, and physical
  contribution withdrawal.
- `dockPersistence.test.ts`: safe split/tab/floating round-trip plus hostile,
  excessive, contradictory-constraint, off-window, and non-finite rejection.
- Existing store, Dockview, template, empty-state, host, and Sidebar suites
  remain regression evidence.

## Failure and Removal

Invalid feature configuration renders an accessible error and is not partially
applied. Invalid persisted roots fall back to defaults; invalid panels are
isolated. Removing a contribution withdraws it from discovery, templates, and
rendering together. Persisted references display the unavailable panel until
removed or the contribution returns. Cleanup never issues a domain job cancel.
