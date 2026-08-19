/**
 * In-memory cache of the connected broker's complete symbol universe.
 *
 * Autocomplete has to answer on every keystroke, so it cannot pay a round trip
 * per character. The universe is read once per session from the cheap
 * `data.symbols` route (names only, no quote evidence), held here at module
 * scope, and shared by every widget that mounts.
 *
 * Nothing here knows what a broker is. The symbols and their ordering come from
 * whichever provider Data resolves at runtime, so swapping MT5 for another
 * broker changes the contents without changing this module.
 */

import { apiClients, unwrapData } from '@/clients';

/** Matches the gateway's `API_MAX_PAGE_SIZE`; larger requests are rejected. */
const PAGE_SIZE = 200;

/**
 * Hard stop on the cursor walk. At `PAGE_SIZE` this admits 20,000 symbols, so
 * a provider that returned a cursor forever fails closed rather than looping.
 */
const MAX_PAGES = 100;

/** Upper bound on rendered suggestions; a longer list is not readable anyway. */
const MAX_SUGGESTIONS = 50;

let cached: string[] | null = null;
let inflight: Promise<string[]> | null = null;

/**
 * Walk every page of the symbol directory.
 *
 * @returns Deduplicated, alphabetically ordered provider symbols.
 */
async function walkSymbolPages(): Promise<string[]> {
  const collected = new Set<string>();
  let cursor: string | undefined;
  let complete = false;

  for (let page = 0; page < MAX_PAGES; page++) {
    const response = await apiClients.data.symbols({ limit: PAGE_SIZE, cursor });
    const symbolPage = unwrapData(response);
    for (const symbol of symbolPage.items) {
      collected.add(symbol);
    }
    if (!symbolPage.next_cursor) {
      complete = true;
      break;
    }
    cursor = symbolPage.next_cursor;
  }

  if (!complete) {
    throw new Error('Symbol universe exceeded the bounded page walk');
  }

  return [...collected].sort((a, b) => a.localeCompare(b));
}

/**
 * Read the broker symbol universe, loading it once per session.
 *
 * Concurrent callers share one in-flight request, so several widgets mounting
 * together cannot each start their own walk. A failed load is not cached: the
 * next caller retries.
 *
 * @returns Every symbol the connected provider exposes.
 */
export function loadSymbolUniverse(): Promise<string[]> {
  if (cached) return Promise.resolve(cached);
  if (inflight) return inflight;

  inflight = walkSymbolPages()
    .then((symbols) => {
      cached = symbols;
      return symbols;
    })
    .finally(() => {
      inflight = null;
    });

  return inflight;
}

/**
 * Discard the cached universe.
 *
 * Call this when the active broker or session changes — the previous provider's
 * symbols are not valid against a new one — and between tests.
 */
export function resetSymbolUniverse(): void {
  cached = null;
  inflight = null;
}

/**
 * Rank universe symbols against what the user has typed so far.
 *
 * Prefix matches come first because a trader typing "EUR" means EURUSD long
 * before they mean XAUEUR; substring matches follow so a partial or mid-symbol
 * fragment still finds its instrument.
 *
 * @param universe Symbols to search.
 * @param term Raw user input.
 * @param limit Maximum suggestions to return.
 * @returns Ordered suggestions, empty when the term is blank.
 */
export function filterSymbols(
  universe: readonly string[],
  term: string,
  limit: number = MAX_SUGGESTIONS
): string[] {
  const needle = term.trim().toUpperCase();
  if (!needle) return [];

  const prefixed: string[] = [];
  const contained: string[] = [];
  for (const symbol of universe) {
    const candidate = symbol.toUpperCase();
    if (candidate.startsWith(needle)) {
      prefixed.push(symbol);
    } else if (candidate.includes(needle)) {
      contained.push(symbol);
    }
    if (prefixed.length >= limit) break;
  }

  return [...prefixed, ...contained].slice(0, limit);
}

/**
 * Resolve typed text to one exact provider-native symbol.
 *
 * Provider spelling is authoritative. A case-insensitive lookup is accepted
 * only when it identifies exactly one symbol, and the original provider value
 * is returned so broker suffixes and casing are never rewritten by the UI.
 *
 * @param universe Symbols supplied by the connected provider.
 * @param candidate Raw user input or a selected suggestion.
 * @returns The exact provider symbol, or null when there is no unique match.
 */
export function resolveSourceSymbol(
  universe: readonly string[],
  candidate: string
): string | null {
  const trimmed = candidate.trim();
  if (!trimmed) return null;

  const exact = universe.find((symbol) => symbol === trimmed);
  if (exact) return exact;

  const folded = trimmed.toUpperCase();
  const matches = universe.filter((symbol) => symbol.toUpperCase() === folded);
  return matches.length === 1 ? matches[0] : null;
}
