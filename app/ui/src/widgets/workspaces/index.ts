/** Public UI seam for Workspace Layout and Session Mode (FEAT-UI-01). */
export { useWorkspaceStore, selectOrderEntryDisabled, selectTradingActivityDisabled, mapRuntimeProfileToAccountMode } from './store';
export type { WorkspaceStoreState } from './store';
export type { Workspace, Widget, WidgetType, GridRect, AccountMode, PlatformAccountMode, SelectableAccountMode, ConfirmationMode } from './contracts';
export {
  MAX_CUSTOM_WORKSPACES,
  WIDGET_TYPES,
  SELECTABLE_ACCOUNT_MODES,
  ACCOUNT_MODE_SETTING_KEY,
  isSelectableAccountMode,
} from './contracts';
export { TemplatePicker } from './TemplatePicker';
export { WorkspaceEmptyState } from './WorkspaceEmptyState';
export { WORKSPACE_TEMPLATES, findWorkspaceTemplate } from './templates';
export type { WorkspaceTemplate, WorkspaceTemplateId, WidgetPreset } from './templates';
export { buildDockLayout, DOCK_WIDGET_COMPONENT } from './dockLayout';
