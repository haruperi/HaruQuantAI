/** Existing menu label and deferred action; no portfolio calculation or mutation. */
export const label = 'Merge WF results';

/** Preserve the label sent to the host's existing deferred-notice callback. */
export function deferAction(deferred: (label: string) => void): void {
  deferred(`Portfolio: ${label}`);
}
