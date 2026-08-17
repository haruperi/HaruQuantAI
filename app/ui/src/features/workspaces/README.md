# Workspaces

## Purpose

Owns non-authoritative workspace layout preference, workspace templates, the
docking layout trees behind them, order-confirmation mode, and account-mode
presentation for `FEAT-UI-01`. See `app/ui/README.md` §4.1 for the full
`FR-UI-001`–`FR-UI-029`, `FR-UI-195`–`FR-UI-199`, and `FR-UI-200`–`FR-UI-202`
requirement tables, and §4.16 for the docking host components.

## Public API

- `useWorkspaceStore`, `selectOrderEntryDisabled`, `mapRuntimeProfileToAccountMode`
  through `index.ts`.
- `TemplatePicker` (new-workspace template picker screen), `WorkspaceEmptyState`
  (explicit empty-workspace prompt), `WORKSPACE_TEMPLATES`,
  `findWorkspaceTemplate`, `buildDockLayout`, `DOCK_WIDGET_COMPONENT`.
- Types: `Workspace`, `Widget`, `WidgetType`, `GridRect`, `AccountMode`,
  `ConfirmationMode`, `WorkspaceTemplate`, `WorkspaceTemplateId`,
  `WidgetPreset`, `MAX_CUSTOM_WORKSPACES`, `WIDGET_TYPES`.

## Notes

- Only `workspaces`/`activeWorkspaceId`/`defaultWorkspaceId` persist to
  `localStorage`; confirmation mode and account mode are session-only and are
  never inherited across a reload.
- `accountMode` is the app-wide trading context: `'sim'`, `'demo'`, `'live'`,
  or `'unknown'`. The operator elects it from the profile dropdown and it is
  persisted server-side as the `ACCOUNT_MODE` system setting, which is the
  single authority for the execution route, the runtime profile stamped onto
  every routed order, and the account state the dashboards read. The store
  learns it two ways, both derived from that one setting: the authenticated
  identity's `runtime_profile` (see `context/auth.tsx`) and the system-settings
  read on mount. Until either resolves it, mode presents as `'unknown'` and
  order entry stays disabled by design (fail closed), not as a placeholder bug.
- `sim` executes virtually against the Simulator; `demo` and `live` both relay
  to the connected MT5 terminal and differ only by the credentials the operator
  configured, so the app-level distinction is registry marking rather than a
  technical gate. Selecting `live` is what puts the application on the live
  route; there is no separate live-enablement flag, and Risk remains the sole
  authority on whether any individual order proceeds.
- `accountModeVersion` is the system-settings record version the mode was read
  from; a mode change writes the complete settings document back under that
  version so a concurrent edit is refused rather than silently overwritten.
- Workspace creation opens a pending workspace (`templateChoicePending`)
  rendered as the template picker; applying a content template seeds its
  widget preset and renames the workspace, while Blank keeps the
  deterministic `New Workspace-N` name (FR-UI-195–FR-UI-197). Template
  presets are EURUSD-bound by owner decision.
- Live layout geometry is a serialized Dockview tree per workspace
  (`dock`), produced by the docking host and rebuilt deterministically from
  legacy grid rectangles when absent (FR-UI-201). The widget list is the
  panel registry; panel ids equal widget ids.

## Verification

- `store.test.ts` provides FR-mapped unit evidence, including dock-layout
  persistence.
- `dockLayout.test.ts` covers the layout factory and legacy migration.
- `TemplatePicker.test.tsx` covers picker rendering, template application,
  and Blank behavior; `WorkspaceEmptyState.test.tsx` covers the empty prompt.
- `src/components/layout/DockingWorkspace.test.tsx` covers the docking host
  adapter (restore paths, reconciliation, persistence, keyboard moves).
