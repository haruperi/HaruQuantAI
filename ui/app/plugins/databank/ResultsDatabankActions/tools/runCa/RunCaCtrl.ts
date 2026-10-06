/** Preserve the latent Run CA deferred action; no analysis popup is enabled. */
export function requestRunCa(deferred: (label: string) => void): void {
  deferred('Tools: Run CA');
}
