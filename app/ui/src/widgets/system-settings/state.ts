/** Draft/conflict helpers for FEAT-UI-SYSTEM_SETTINGS. */

export interface SettingDiff {
  readonly key: string;
  readonly before: string | undefined;
  readonly after: string | undefined;
}

export function diffSettings(
  original: Readonly<Record<string, string>>,
  draft: Readonly<Record<string, string>>,
): SettingDiff[] {
  const keys = new Set([...Object.keys(original), ...Object.keys(draft)]);
  return [...keys]
    .filter((key) => original[key] !== draft[key])
    .sort()
    .map((key) => ({ key, before: original[key], after: draft[key] }));
}

export function isSettingsDirty(
  original: Readonly<Record<string, string>>,
  draft: Readonly<Record<string, string>>,
): boolean {
  return diffSettings(original, draft).length > 0;
}

export function settingsFailureMessage(code: string): string {
  if (code === "SETTINGS_CONFLICT") {
    return "Settings changed elsewhere. Reload the current revision before applying this draft.";
  }
  if (code === "CAPABILITY_UNAVAILABLE" || code === "UPSTREAM_UNAVAILABLE") {
    return "Settings are currently unavailable; your unsaved draft has been kept.";
  }
  return "The settings owner rejected this update; your unsaved draft has been kept.";
}
