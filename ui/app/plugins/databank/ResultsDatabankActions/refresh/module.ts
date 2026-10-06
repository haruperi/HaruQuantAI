/** Preserve notification-only prototype refresh; no backend reload is performed. */
export function refreshDatabank(notify: (message: string) => void): void {
  notify('Databank reloaded');
}
