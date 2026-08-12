'use client';

import React, { useEffect, useState } from 'react';
import { useTradingStore } from '../../store/useTradingStore';
import { useWorkspaceStore } from '../workspaces';
import { apiClients, unwrapData, type MarketRow, type Watchlist } from '@/clients';
import { MoreVertical, LineChart, AlignJustify, Layers } from 'lucide-react';

// Fixed classification (not sourced from src/mock/ - that would reintroduce
// fixture data into a production module, NFR-UI-007). A class with nothing
// in the directory is a legitimate, truthfully-empty filter (FR-UI-034),
// not a reason to hide the pill.
const MARKET_CATEGORIES = ['Forex', 'Commodities', 'Indices', 'Stocks', 'Cryptocurrencies'];

/**
 * Derived display row built from a real market-directory row.
 *
 * `apiClients.data.markets()` never composes Indicators-owned technical
 * overlays (volatility/ADR/range/change-in-pips) - that projection only runs
 * when a caller opts in via `quotes(..., { includeTechnicals: true })`, which
 * this directory browse deliberately doesn't do (FR-UI-030: no client-side
 * calculation, and no field this widget can't get straight from the API).
 */
interface DisplayRow {
  symbol: string;
  name: string;
  assetClass: string;
  decimals: number;
  last: number | null;
  change: number | null;
  changePercent: number | null;
  open: number | null;
  high: number | null;
  low: number | null;
  volume: number | null;
}

/** Map one API row into a display row. */
function toDisplayRow(row: MarketRow): DisplayRow {
  return {
    symbol: row.symbol,
    name: row.name,
    assetClass: row.asset_class,
    decimals: row.digits ?? 2,
    last: row.last,
    change: row.change,
    changePercent: row.change_percent,
    open: row.open,
    high: row.high,
    low: row.low,
    volume: row.volume,
  };
}

// Bound provider work and render each page as soon as it resolves. Capped at
// a fixed number of pages so this never degrades into walking the whole
// broker catalogue - the same anti-pattern the watchlist-scoped quote fetch
// (see WatchlistWidget) already avoids at a smaller scale.
const MARKETS_PAGE_SIZE = 50;
const MARKETS_MAX_PAGES = 4;

type SortKey = 'Symbol' | 'Change' | 'Volume';

export const MarketsWidget: React.FC = () => {
  const [selectedCategory, setSelectedCategory] = useState<string>('Forex');
  const [sortBy, setSortBy] = useState<SortKey>('Volume');
  const [activeMenuSymbol, setActiveMenuSymbol] = useState<string | null>(null);
  const [directory, setDirectory] = useState<DisplayRow[]>([]);
  const [status, setStatus] = useState<'loading' | 'ready' | 'error'>('loading');
  const [errorMsg, setErrorMsg] = useState('');

  const [watchlists, setWatchlists] = useState<Watchlist[]>([]);
  // null = no watchlist filter ("All Instruments"); the directory itself
  // stays the data source either way, this only narrows what's shown.
  const [activeWatchlistId, setActiveWatchlistId] = useState<string | null>(null);

  const { openOrderTicket, submitOrder } = useTradingStore();
  const { orderConfirmationRequired, addWidgetToWorkspace } = useWorkspaceStore();

  // Load the caller's watchlists for the optional quick-filter selector
  // below. This is additive to the directory fetch, not a replacement for
  // it - Markets keeps presenting the tradable directory (FR-UI-033) even
  // when no watchlist is selected.
  useEffect(() => {
    let cancelled = false;
    void apiClients.watchlists
      .list()
      .then((response) => {
        if (cancelled) return;
        setWatchlists(unwrapData(response));
      })
      .catch(() => {
        // Non-fatal: the watchlist filter is just unavailable, the directory
        // still loads and renders normally.
      });
    return () => {
      cancelled = true;
    };
  }, []);

  // Load the tradable instrument directory for the configured runtime source
  // (source_id is never passed - the backend resolves the configured
  // default; the UI never elects it, same rule as account mode). Pages are
  // appended as they resolve so the table fills in progressively.
  useEffect(() => {
    let cancelled = false;
    setStatus('loading');
    setDirectory([]);
    setErrorMsg('');

    const loadPages = async (): Promise<void> => {
      try {
        let cursor: string | undefined;
        for (let page = 0; page < MARKETS_MAX_PAGES; page++) {
          const response = await apiClients.data.markets({ limit: MARKETS_PAGE_SIZE, cursor });
          if (cancelled) return;
          const directoryPage = unwrapData(response);
          setDirectory((current) => [...current, ...directoryPage.rows.map(toDisplayRow)]);
          if (!directoryPage.next_cursor) break;
          cursor = directoryPage.next_cursor;
        }
        if (!cancelled) setStatus('ready');
      } catch {
        if (cancelled) return;
        setErrorMsg('Unable to load the market directory.');
        setStatus('error');
      }
    };

    void loadPages();
    return () => {
      cancelled = true;
    };
  }, []);

  const activeWatchlist = watchlists.find((item) => item.watchlist_id === activeWatchlistId) ?? null;
  const watchlistSymbols = activeWatchlist ? new Set(activeWatchlist.items.map((item) => item.symbol)) : null;

  const filteredProducts = directory.filter(
    (p) => p.assetClass === selectedCategory && (!watchlistSymbols || watchlistSymbols.has(p.symbol))
  );

  // Symbol/Change/Volume per FR-UI-035; every ordering falls back to a
  // symbol tiebreak so equal values render deterministically rather than
  // relying on incidental array order.
  const sortedProducts = [...filteredProducts].sort((a, b) => {
    const primary =
      sortBy === 'Volume'
        ? (b.volume ?? -1) - (a.volume ?? -1)
        : sortBy === 'Change'
          ? Math.abs(b.changePercent ?? 0) - Math.abs(a.changePercent ?? 0)
          : a.symbol.localeCompare(b.symbol);
    return primary !== 0 ? primary : a.symbol.localeCompare(b.symbol);
  });

  /** Format a nullable numeric cell, or an em-dash when evidence is absent. */
  const fmt = (value: number | null, p: DisplayRow): string =>
    value === null || value === undefined || Number.isNaN(value) ? '—' : value.toFixed(p.decimals ?? 2);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Active Watchlist Filter */}
      <div style={{ padding: '6px 10px', background: 'var(--cme-navy-dark)', borderBottom: '1px solid var(--cme-navy-border)', display: 'flex', alignItems: 'center', gap: '8px' }}>
        <span style={{ fontWeight: 700, fontSize: '11px', color: 'var(--text-muted)' }}>WATCHLIST:</span>
        <select
          className="form-select"
          value={activeWatchlistId ?? ''}
          onChange={(e) => setActiveWatchlistId(e.target.value || null)}
          style={{ padding: '2px 6px', fontSize: '11px' }}
        >
          <option value="">All Instruments</option>
          {watchlists.map((item) => (
            <option key={item.watchlist_id} value={item.watchlist_id}>
              {item.name}
              {item.is_default ? ' (default)' : ''}
            </option>
          ))}
        </select>
      </div>

      {/* Category Pills Bar */}
      <div className="category-pills">
        {MARKET_CATEGORIES.map((cat) => (
          <div
            key={cat}
            className={`category-pill ${cat === selectedCategory ? 'active' : ''}`}
            onClick={() => setSelectedCategory(cat)}
          >
            {cat}
          </div>
        ))}
      </div>

      {/* Sub-header Sort Dropdown */}
      <div style={{ display: 'flex', justifyContent: 'flex-end', padding: '6px 10px', background: 'var(--cme-navy-dark)', borderBottom: '1px solid var(--cme-navy-border)' }}>
        <select
          className="form-select"
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value as SortKey)}
          style={{ padding: '2px 8px', fontSize: '11px' }}
        >
          <option value="Volume">Sort by Volume</option>
          <option value="Change">Sort by Change %</option>
          <option value="Symbol">Sort by Symbol</option>
        </select>
      </div>

      {/* Main Markets Table */}
      <div style={{ flex: 1, overflow: 'auto' }}>
        {status === 'loading' && directory.length === 0 && (
          <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted, #718294)' }}>
            Loading the market directory…
          </div>
        )}
        {status === 'error' && (
          <div role="alert" style={{ padding: '8px 24px', textAlign: 'center', color: 'var(--financial-negative, #ff4975)' }}>
            {errorMsg}
          </div>
        )}
        {status === 'ready' && sortedProducts.length === 0 && (
          <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted, #718294)' }}>
            No symbols available for {selectedCategory}{activeWatchlist ? ` in ${activeWatchlist.name}` : ''}.
          </div>
        )}
        {directory.length > 0 && sortedProducts.length > 0 && (
        <table className="cme-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Last Price</th>
              <th>Change</th>
              <th>Open</th>
              <th>High</th>
              <th>Low</th>
              <th style={{ textAlign: 'center' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {sortedProducts.map((p) => {
              const isUp = (p.change ?? 0) > 0;
              const isDown = (p.change ?? 0) < 0;
              const priceClass = isUp ? 'price-up' : isDown ? 'price-down' : 'price-flat';
              const changeCell =
                p.change === null || p.changePercent === null
                  ? '—'
                  : `${isUp ? '+' : ''}${p.change.toFixed(p.decimals)} (${p.changePercent >= 0 ? '+' : ''}${p.changePercent.toFixed(2)}%)`;

              return (
                <tr key={p.symbol}>
                  <td style={{ fontWeight: 600 }}>{p.name}</td>
                  <td className={priceClass}>{fmt(p.last, p)}</td>
                  <td className={priceClass}>{changeCell}</td>
                  <td style={{ fontFamily: 'var(--font-mono)' }}>{fmt(p.open, p)}</td>
                  <td style={{ fontFamily: 'var(--font-mono)' }}>{fmt(p.high, p)}</td>
                  <td style={{ fontFamily: 'var(--font-mono)' }}>{fmt(p.low, p)}</td>
                  <td style={{ textAlign: 'center', position: 'relative' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '4px' }}>
                      <button
                        className="btn-cme btn-outline btn-sm"
                        onClick={() => {
                          if (!orderConfirmationRequired) {
                            submitOrder({ symbol: p.symbol, side: 'BUY', qty: 1, orderType: 'Market' });
                          } else {
                            openOrderTicket({ symbol: p.symbol, side: 'BUY', type: 'Market' });
                          }
                        }}
                      >
                        TRADE
                      </button>
                      <button
                        className="btn-cme btn-outline btn-sm"
                        style={{ padding: '2px 4px' }}
                        onClick={() => setActiveMenuSymbol(activeMenuSymbol === p.symbol ? null : p.symbol)}
                      >
                        <MoreVertical size={14} />
                      </button>
                    </div>

                    {/* Context Menu Popup */}
                    {activeMenuSymbol === p.symbol && (
                      <div className="markets-row-menu">
                        <div
                          className="sidebar-menu-item"
                          onClick={() => {
                            addWidgetToWorkspace('chart', `${p.symbol} Chart`, p.symbol);
                            setActiveMenuSymbol(null);
                          }}
                        >
                          <LineChart size={14} /> Chart
                        </div>
                        <div
                          className="sidebar-menu-item"
                          onClick={() => {
                            addWidgetToWorkspace('priceLadder', `${p.symbol} DOM`, p.symbol);
                            setActiveMenuSymbol(null);
                          }}
                        >
                          <AlignJustify size={14} /> Price Ladder
                        </div>
                        {/* Options Grid has no owning backend domain (FEAT-UI-07,
                            README §6) - unavailable for every row, not a
                            per-symbol guess, so it stays disabled everywhere. */}
                        <div
                          className="sidebar-menu-item disabled"
                          aria-disabled="true"
                          title="Options are not available yet"
                          style={{ opacity: 0.4, cursor: 'not-allowed' }}
                        >
                          <Layers size={14} /> Options
                        </div>
                      </div>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        )}
      </div>
    </div>
  );
};
