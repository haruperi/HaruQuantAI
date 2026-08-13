'use client';

import React, { useEffect, useState } from 'react';
import { useTradingStore } from '../../store/useTradingStore';
import { useWorkspaceStore } from '../workspaces';
import { apiClients, unwrapData, type MarketRow, type Watchlist } from '@/clients';
import { MoreVertical, LineChart, AlignJustify, Layers } from 'lucide-react';

import { CmeProgressBar } from '../../components/common/CmeProgressBar';

// Fixed classification (not sourced from src/mock/ - that would reintroduce
// fixture data into a production module, NFR-UI-007). A class with nothing
// in the directory is a legitimate, truthfully-empty filter (FR-UI-034),
// not a reason to hide the pill.
const MARKET_CATEGORIES = ['Forex', 'Commodities', 'Indices', 'Stocks', 'Cryptocurrencies'];

/**
 * Derived display row built from a real market-directory row.
 *
 * Both directory and explicit-watchlist reads opt in to Indicators-owned
 * technical overlays. The widget only formats the API evidence and performs
 * no market calculations (FR-UI-030).
 */
interface DisplayRow {
  symbol: string;
  name: string;
  assetClass: string;
  decimals: number;
  last: number | null;
  change: number | null;
  changePercent: number | null;
  changePips: number | null;
  volatility: number | null;
  adr: number | null;
  range: number | null;
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
    changePips: row.change_pips ?? null,
    volatility: row.volatility ?? null,
    adr: row.adr ?? null,
    range: row.range_percent_of_adr ?? null,
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

type SortKey = 'Symbol' | 'Change' | 'Volatility' | 'ADR' | 'Range';

export const MarketsWidget: React.FC = () => {
  const [selectedCategory, setSelectedCategory] = useState<string>('Forex');
  const [sortBy, setSortBy] = useState<SortKey>('Symbol');
  const [activeMenuSymbol, setActiveMenuSymbol] = useState<string | null>(null);
  const [directory, setDirectory] = useState<DisplayRow[]>([]);
  const [status, setStatus] = useState<'loading' | 'ready' | 'error'>('loading');
  const [errorMsg, setErrorMsg] = useState('');
  const [loadProgress, setLoadProgress] = useState<{ value: number; max: number; label: string }>({
    value: 0,
    max: 100,
    label: 'Loading market directory…',
  });

  const [watchlists, setWatchlists] = useState<Watchlist[]>([]);
  // null = no watchlist filter ("All Instruments"); the directory itself
  // stays the data source either way, this only narrows what's shown.
  const [activeWatchlistId, setActiveWatchlistId] = useState<string | null>(null);

  const { openOrderTicket, submitOrder } = useTradingStore();
  const { orderConfirmationRequired, addWidgetToWorkspace } = useWorkspaceStore();

  const [watchlistsLoaded, setWatchlistsLoaded] = useState(false);

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
        const list = unwrapData(response);
        setWatchlists(list);
        const defaultWl =
          list.find((w) => w.is_default) ??
          list.find((w) => w.name.toLowerCase() === 'default') ??
          list[0];
        if (defaultWl) {
          setActiveWatchlistId(defaultWl.watchlist_id);
        }
      })
      .catch(() => {
        // Non-fatal: the watchlist filter is just unavailable, the directory
        // still loads and renders normally.
      })
      .finally(() => {
        if (!cancelled) setWatchlistsLoaded(true);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const activeWatchlist =
    watchlists.find((item) => item.watchlist_id === activeWatchlistId) ??
    watchlists.find((item) => item.is_default) ??
    watchlists[0] ??
    null;

  // Load quotes with technical overlays for symbols in the active watchlist,
  // matching the calculation in tests/api/usage/12_markets.py.
  useEffect(() => {
    if (!watchlistsLoaded) return;
    let cancelled = false;
    setStatus('loading');
    setDirectory([]);
    setErrorMsg('');
    setLoadProgress({ value: 5, max: 100, label: 'Connecting to market directory…' });

    const loadData = async (): Promise<void> => {
      try {
        if (activeWatchlist && activeWatchlist.items.length > 0) {
          const symbols = activeWatchlist.items.map((item) => item.symbol);
          const BATCH_SIZE = 3;
          const totalBatches = Math.ceil(symbols.length / BATCH_SIZE);

          for (let b = 0; b < totalBatches; b++) {
            const batchSymbols = symbols.slice(b * BATCH_SIZE, (b + 1) * BATCH_SIZE);
            const startPct = Math.round((b / totalBatches) * 100);
            setLoadProgress({
              value: Math.max(startPct, 10),
              max: 100,
              label: `Loading quotes (${b + 1} of ${totalBatches} batches)…`,
            });

            const response = await apiClients.data.quotes(batchSymbols, { includeTechnicals: true });
            if (cancelled) return;
            const directoryPage = unwrapData(response);
            const batchRows = directoryPage.rows.map(toDisplayRow);

            setDirectory((current) => [...current, ...batchRows]);
            const endPct = Math.round(((b + 1) / totalBatches) * 100);
            setLoadProgress({
              value: endPct,
              max: 100,
              label: `Loaded batch ${b + 1} of ${totalBatches} (${endPct}%)`,
            });
          }
          if (!cancelled) setStatus('ready');
        } else {
          let cursor: string | undefined;
          for (let page = 0; page < MARKETS_MAX_PAGES; page++) {
            const startPct = Math.round((page / MARKETS_MAX_PAGES) * 100);
            setLoadProgress({
              value: Math.max(startPct, 15),
              max: 100,
              label: `Loading market directory (Page ${page + 1} of ${MARKETS_MAX_PAGES})…`,
            });

            const response = await apiClients.data.markets({ limit: MARKETS_PAGE_SIZE, cursor, includeTechnicals: true });
            if (cancelled) return;
            const directoryPage = unwrapData(response);
            setDirectory((current) => [...current, ...directoryPage.rows.map(toDisplayRow)]);

            const endPct = Math.round(((page + 1) / MARKETS_MAX_PAGES) * 100);
            setLoadProgress({
              value: endPct,
              max: 100,
              label: `Loaded Page ${page + 1} of ${MARKETS_MAX_PAGES} (${endPct}%)`,
            });

            if (!directoryPage.next_cursor) {
              setLoadProgress({ value: 100, max: 100, label: 'Loaded all symbols (100%)' });
              break;
            }
            cursor = directoryPage.next_cursor;
          }
          if (!cancelled) setStatus('ready');
        }
      } catch {
        if (cancelled) return;
        setErrorMsg('Unable to load the market directory.');
        setStatus('error');
      }
    };

    void loadData();
    return () => {
      cancelled = true;
    };
  }, [watchlistsLoaded, activeWatchlistId, activeWatchlist]);

  const watchlistSymbols = activeWatchlist ? new Set(activeWatchlist.items.map((item) => item.symbol)) : null;

  // Build category set dynamically from active watchlist items & directory map
  const activeCategories = React.useMemo(() => {
    if (!activeWatchlist || activeWatchlist.items.length === 0) {
      return MARKET_CATEGORIES;
    }
    const directoryClassBySymbol = new Map(directory.map((d) => [d.symbol, d.assetClass]));
    const categorySet = new Set<string>();
    for (const item of activeWatchlist.items) {
      const cls = item.asset_class || directoryClassBySymbol.get(item.symbol);
      if (cls && cls !== 'Other') {
        categorySet.add(cls);
      }
    }
    const filtered = MARKET_CATEGORIES.filter((cat) => categorySet.has(cat));
    return filtered.length > 0 ? filtered : MARKET_CATEGORIES;
  }, [activeWatchlist, directory]);

  // Keep selectedCategory synced with activeCategories
  useEffect(() => {
    if (activeCategories.length > 0 && !activeCategories.includes(selectedCategory)) {
      setSelectedCategory(activeCategories[0]);
    }
  }, [activeCategories, selectedCategory]);

  const filteredProducts = directory.filter(
    (p) => p.assetClass === selectedCategory && (!watchlistSymbols || watchlistSymbols.has(p.symbol))
  );

  // Symbol/Change/Volatility/ADR/Range sorting with a stable symbol tiebreak.
  const sortedProducts = [...filteredProducts].sort((a, b) => {
    let primary = 0;
    if (sortBy === 'Change') {
      primary = Math.abs(b.changePercent ?? 0) - Math.abs(a.changePercent ?? 0);
    } else if (sortBy === 'Volatility') {
      primary = (b.volatility ?? -1) - (a.volatility ?? -1);
    } else if (sortBy === 'ADR') {
      primary = (b.adr ?? -1) - (a.adr ?? -1);
    } else if (sortBy === 'Range') {
      const rangeA = a.range ?? (a.high !== null && a.low !== null ? a.high - a.low : -1);
      const rangeB = b.range ?? (b.high !== null && b.low !== null ? b.high - b.low : -1);
      primary = rangeB - rangeA;
    } else {
      primary = a.symbol.localeCompare(b.symbol);
    }
    return primary !== 0 ? primary : a.symbol.localeCompare(b.symbol);
  });

  function getRangeColor(range: number | null | undefined): string | undefined {
  if (range === null || range === undefined || Number.isNaN(range)) {
    return undefined;
  }
  if (range <= 40) return '#00e473';  // Green
  if (range <= 60) return '#29b6f6';  // Blue
  if (range <= 80) return '#ffca28';  // Yellow
  if (range <= 100) return '#ff9800'; // Orange
  return '#ff003d';                    // Red (> 100)
}

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
          onChange={(e) => setActiveWatchlistId(e.target.value)}
          style={{ padding: '2px 6px', fontSize: '11px' }}
        >
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
        {activeCategories.map((cat) => (
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
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '6px', padding: '6px 10px', background: 'var(--cme-navy-dark)', borderBottom: '1px solid var(--cme-navy-border)' }}>
        <span style={{ fontWeight: 700, fontSize: '11px', color: 'var(--text-muted)' }}>Sort By:</span>
        <select
          className="form-select"
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value as SortKey)}
          style={{ padding: '2px 8px', fontSize: '11px' }}
        >
          <option value="Symbol">Symbol</option>
          <option value="Change">Change</option>
          <option value="Volatility">Volatility</option>
          <option value="ADR">ADR</option>
          <option value="Range">Range</option>
        </select>
      </div>

      {/* Main Markets Table */}
      <div style={{ flex: 1, overflow: 'auto' }}>
        {status === 'loading' && (
          <div style={{ padding: directory.length === 0 ? '32px 24px' : '10px 16px', maxWidth: directory.length === 0 ? '480px' : '100%', margin: directory.length === 0 ? '0 auto' : '0' }}>
            <CmeProgressBar
              value={loadProgress.value}
              max={loadProgress.max}
              label={loadProgress.label}
              subtext={`${loadProgress.value}%`}
              variant="blue"
              height={directory.length === 0 ? 10 : 6}
            />
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
              <th>Symbol</th>
              <th>Last Price</th>
              <th>Change</th>
              <th>Volatility</th>
              <th>ADR</th>
              <th>Range</th>
              <th>Open</th>
              <th>High</th>
              <th>Low</th>
              <th style={{ textAlign: 'center' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {sortedProducts.map((p) => {
              const changeVal = p.changePercent ?? p.changePips ?? p.change ?? 0;
              const isUp = changeVal > 0;
              const isDown = changeVal < 0;
              const priceClass = isUp ? 'price-up' : isDown ? 'price-down' : 'price-flat';

              const pipsOrChangeStr =
                p.changePips !== null && p.changePips !== undefined
                  ? `${p.changePips > 0 ? '+' : ''}${p.changePips.toFixed(1)}`
                  : p.change !== null && p.change !== undefined
                    ? `${p.change > 0 ? '+' : ''}${p.change.toFixed(p.decimals)}`
                    : '';

              const percentStr =
                p.changePercent !== null && p.changePercent !== undefined
                  ? ` (${p.changePercent > 0 ? '+' : ''}${p.changePercent.toFixed(2)}%)`
                  : '';

              const changeCell =
                (p.change === null || p.change === undefined) &&
                (p.changePercent === null || p.changePercent === undefined) &&
                (p.changePips === null || p.changePips === undefined)
                  ? '—'
                  : `${pipsOrChangeStr}${percentStr}`;

              const volCell = p.volatility !== null && p.volatility !== undefined ? `${(p.volatility * 100).toFixed(2)}%` : '—';
              const adrCell = p.adr !== null && p.adr !== undefined ? p.adr.toFixed(1) : '—';
              const rangeCell = p.range !== null && p.range !== undefined ? `${p.range.toFixed(1)}%` : '—';

              const changeColor = isUp
                ? 'var(--financial-positive, #00e473)'
                : isDown
                  ? 'var(--financial-negative, #ff003d)'
                  : 'var(--text-white, #ffffff)';

              const rangeColor = getRangeColor(p.range);

              return (
                <tr key={p.symbol}>
                  <td style={{ fontWeight: 600 }}>{p.symbol}</td>
                  <td className={priceClass} style={{ color: changeColor }}>{fmt(p.last, p)}</td>
                  <td className={priceClass} style={{ color: changeColor, fontWeight: 600 }}>{changeCell}</td>
                  <td style={{ fontFamily: 'var(--font-mono)' }}>{volCell}</td>
                  <td style={{ fontFamily: 'var(--font-mono)' }}>{adrCell}</td>
                  <td style={{ fontFamily: 'var(--font-mono)', color: rangeColor, fontWeight: rangeColor ? 600 : 'normal' }}>{rangeCell}</td>
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
