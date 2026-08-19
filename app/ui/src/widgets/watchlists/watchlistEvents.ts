/** Browser-local invalidation boundary for independently mounted watchlist consumers. */
export const WATCHLISTS_CHANGED_EVENT = 'haruquant:watchlists-changed';

/** Notify active widgets that authoritative watchlist data changed. */
export function emitWatchlistsChanged(): void {
  window.dispatchEvent(new Event(WATCHLISTS_CHANGED_EVENT));
}
