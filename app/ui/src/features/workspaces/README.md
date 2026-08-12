# Workspaces

## Purpose

Owns non-authoritative workspace layout preference, order-confirmation mode, and
account-mode presentation for `FEAT-UI-01`. See `app/ui/README.md` §4.1 for the
full `FR-UI-001`–`FR-UI-029` requirement table.

## Public API

- `useWorkspaceStore`, `selectOrderEntryDisabled`, `mapRuntimeProfileToAccountMode`
  through `index.ts`.
- Types: `Workspace`, `Widget`, `WidgetType`, `GridRect`, `AccountMode`,
  `ConfirmationMode`, `MAX_CUSTOM_WORKSPACES`, `WIDGET_TYPES`.

## Notes

- Only `workspaces`/`activeWorkspaceId`/`defaultWorkspaceId` persist to
  `localStorage`; confirmation mode and account mode are session-only and are
  never inherited across a reload.
- `accountMode` is derived exclusively from the authenticated identity's
  `runtime_profile` (see `context/auth.tsx`); nothing else may set it. Until
  the API returns that field, mode presents as `'unknown'` and order entry
  stays disabled by design (fail closed), not as a placeholder bug.

## Verification

- `store.test.ts` provides FR-mapped unit evidence.
