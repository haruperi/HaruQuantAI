/** Public UI seam for Workspace Layout and Session Mode (FEAT-UI-01). */
export { useWorkspaceStore, selectOrderEntryDisabled, mapRuntimeProfileToAccountMode } from './store';
export type { WorkspaceStoreState } from './store';
export type { Workspace, Widget, WidgetType, GridRect, AccountMode, ConfirmationMode } from './contracts';
export { MAX_CUSTOM_WORKSPACES, WIDGET_TYPES } from './contracts';
