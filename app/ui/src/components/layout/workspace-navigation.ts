/** Capability-aware navigation helpers for FEAT-UI-WORKSPACE_NAVIGATION. */

export interface NavigationSource {
  readonly id: string;
  readonly label: string;
  readonly title?: string;
  readonly requiredCapabilities: readonly string[];
}

export interface NavigationCommand {
  readonly id: string;
  readonly label: string;
  readonly title?: string;
  readonly available: boolean;
  readonly reason: string | null;
}

/** Build navigation from registered metadata and a current capability snapshot. */
export function buildNavigationCommands(
  sources: readonly NavigationSource[],
  availableCapabilities: ReadonlySet<string>,
): NavigationCommand[] {
  return sources.map((source) => {
    const missing = source.requiredCapabilities.filter(
      (capability) => !availableCapabilities.has(capability),
    );
    return {
      id: source.id,
      label: source.label,
      title: source.title,
      available: missing.length === 0,
      reason:
        missing.length === 0
          ? null
          : `Unavailable: missing ${missing.join(", ")}`,
    };
  });
}

/** Activate one command using standard button keyboard semantics. */
export function isNavigationActivationKey(key: string): boolean {
  return key === "Enter" || key === " ";
}

/** Return the first visible focus target after a panel/command disappears. */
export function nextFocusTarget(
  preferred: HTMLElement | null,
  fallback: HTMLElement | null,
): HTMLElement | null {
  if (preferred?.isConnected && !preferred.hidden) return preferred;
  if (fallback?.isConnected && !fallback.hidden) return fallback;
  return null;
}
