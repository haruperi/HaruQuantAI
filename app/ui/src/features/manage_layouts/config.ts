/**
 * Strict configuration parser for FEAT-UI-MANAGE_LAYOUTS (README §5 keys).
 */

export interface ManageLayoutsConfig {
  readonly defaultWorkspaceTemplate: string | null;
  readonly maxRestoredTabs: number;
  readonly layoutSchemaVersion: number;
  readonly layoutAutosaveIntervalMs: number;
}

const ALLOWED_CONFIG_KEYS = new Set([
  "default_workspace_template",
  "max_restored_tabs",
  "layout_schema_version",
  "layout_autosave_interval_ms",
]);

export function parseManageLayoutsConfig(
  raw?: Record<string, unknown>
): ManageLayoutsConfig {
  if (!raw) {
    return {
      defaultWorkspaceTemplate: null,
      maxRestoredTabs: 20,
      layoutSchemaVersion: 1,
      layoutAutosaveIntervalMs: 1000,
    };
  }

  const unknownKeys = Object.keys(raw).filter(
    (k) => !ALLOWED_CONFIG_KEYS.has(k)
  );
  if (unknownKeys.length > 0) {
    throw new Error(
      `Unknown configuration keys for ManageLayouts: ${unknownKeys.sort().join(", ")}`
    );
  }

  const defaultWorkspaceTemplate =
    typeof raw.default_workspace_template === "string"
      ? raw.default_workspace_template
      : null;
  const maxRestoredTabs =
    typeof raw.max_restored_tabs === "number" &&
    Number.isInteger(raw.max_restored_tabs) &&
    raw.max_restored_tabs >= 1 &&
    raw.max_restored_tabs <= 20
      ? raw.max_restored_tabs
      : 20;
  const layoutSchemaVersion =
    typeof raw.layout_schema_version === "number" &&
    Number.isInteger(raw.layout_schema_version) &&
    raw.layout_schema_version >= 1
      ? raw.layout_schema_version
      : 1;
  const layoutAutosaveIntervalMs =
    typeof raw.layout_autosave_interval_ms === "number" &&
    Number.isInteger(raw.layout_autosave_interval_ms) &&
    raw.layout_autosave_interval_ms >= 250
      ? raw.layout_autosave_interval_ms
      : 1000;

  return {
    defaultWorkspaceTemplate,
    maxRestoredTabs,
    layoutSchemaVersion,
    layoutAutosaveIntervalMs,
  };
}
