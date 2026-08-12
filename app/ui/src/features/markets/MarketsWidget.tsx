'use client';

import React, { useEffect, useState } from 'react';
import { useTradingStore } from '../../store/useTradingStore';
import { useWorkspaceStore } from '../workspaces';
import { assetClasses } from '../../mock/productsData';
import { apiClients, unwrapData, type MarketRow, type Watchlist } from '@/clients';
import { MoreVertical, LineChart, AlignJustify, Layers } from 'lucide-react';

/**
 * Derived display row built from a real market-directory row.
 *
 * Volatility (annualized, %), ADR (10-session average daily range, in pips),
 * and Range (today's range as % of that ADR) are API-composed overlays from
 * Data's D1 bars plus Indicators' formulas, requested via
 * `includeTechnicals`. Any leg may be `null` when a symbol lacks enough
 * history; the table renders an em-dash for those.
 */
interface DisplayRow {
  symbol: string;
  name: string;
  assetClass: string;
  decimals: number;
  last: number | null;
  change: number | null;
  changePips: number | null;
  changePercent: number | null;
  open: number | null;
  high: number | null;
  low: number | null;
  volume: number | null;
  range: number | null;
  rangePct: number | null;
  adr: number | null;
  volatility: number | null;
}

/** Map one API row into a display row. */
function toDisplayRow(row: MarketRow): DisplayRow {
  const high = row.high;
  const low = row.low;
  const range = high !== null && low !== null ? high - low : null;
  return {
    symbol: row.symbol,
    name: row.name,
    assetClass: row.asset_class,
    decimals: row.digits ?? 2,
    last: row.last,
    change: row.change,
    changePips: row.change_pips ?? null,
    changePercent: row.change_percent,
    open: row.open,
    high,
    low,
    volume: row.volume,
    range,
    rangePct: row.range_percent_of_adr ?? null,
    adr: row.adr ?? null,
    volatility: row.volatility ?? null,
  };
}

// Bound provider work and render each batch as soon as it resolves. Sequential
// batches avoid opening concurrent broker sessions for large watchlists.
const QUOTE_BATCH_SIZE = 4;

export const MarketsWidget: React.FC = () => {
  const [selectedCategory, setSelectedCategory] = useState<string>('Forex');
  const [sortBy, setSortBy] = useState<string>('Volume');
  const [activeMenuSymbol, setActiveMenuSymbol] = useState<string | null>(null);
  const [directory, setDirectory] = useState<DisplayRow[]>([]);
  const [status, setStatus] = useState<'loading' | 'ready' | 'error'>('loading');
  const [errorMsg, setErrorMsg] = useState('');

  const [watchlists, setWatchlists] = useState<Watchlist[]>([]);
  const [activeWatchlistId, setActiveWatchlistId] = useState<string | null>(null);

  const { openOrderTicket, submitOrder } = useTradingStore();
  const { orderConfirmationRequired, addWidgetToWorkspace } = useWorkspaceStore();

  // Load the caller's watchlists on mount and select the account's default
  // watchlist as the initial active one; the backend seeds it on first read,
  // so this always resolves to at least one watchlist.
  useEffect(() => {
    let cancelled = false;
    void apiClients.watchlists
      .list()
      .then((response) => {
        if (cancelled) return;
        const lists = unwrapData(response);
        setWatchlists(lists);
        const defaultList = lists.find((item) => item.is_default) ?? lists[0];
        setActiveWatchlistId(defaultList ? defaultList.watchlist_id : null);
      })
      .catch(() => {
        if (cancelled) return;
        setErrorMsg('Unable to load watchlists.');
        setStatus('error');
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const activeWatchlist = watchlists.find((item) => item.watchlist_id === activeWatchlistId) ?? null;
  const activeSymbols = activeWatchlist ? activeWatchlist.items.map((item) => item.symbol) : [];

  // Fetch quotes for exactly the active watchlist's symbols. Unlike the old
  // limit=200 full-catalog fetch, this scales with the watchlist size (~56
  // symbols by default) instead of the broker's entire universe.
  useEffect(() => {
    if (activeSymbols.length === 0) {
      setDirectory([]);
      if (activeWatchlistId !== null) setStatus('ready');
      return;
    }
    let cancelled = false;
    setStatus('loading');
    setDirectory([]);

    const loadBatches = async (): Promise<void> => {
      try {
        for (let index = 0; index < activeSymbols.length; index += QUOTE_BATCH_SIZE) {
          const symbols = activeSymbols.slice(index, index + QUOTE_BATCH_SIZE);
          const response = await apiClients.data.quotes(symbols, { includeTechnicals: true });
          if (cancelled) return;
          const page = unwrapData(response);
          setDirectory((current) => [...current, ...page.rows.map(toDisplayRow)]);
        }
        if (!cancelled) setStatus('ready');
      } catch {
        if (cancelled) return;
        setErrorMsg('Unable to load quotes for the active watchlist.');
        setStatus('error');
      }
    };

    void loadBatches();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeWatchlistId, activeSymbols.join(',')]);

  const filteredProducts = directory.filter((p) => p.assetClass === selectedCategory);

  const sortedProducts = [...filteredProducts].sort((a, b) => {
    if (sortBy === 'Volume') return (b.volume ?? -1) - (a.volume ?? -1);
    if (sortBy === 'Change') return Math.abs(b.changePercent ?? 0) - Math.abs(a.changePercent ?? 0);
    if (sortBy === 'Volatility') return (b.volatility ?? -1) - (a.volatility ?? -1);
    if (sortBy === 'ADR') return (b.adr ?? -1) - (a.adr ?? -1);
    if (sortBy === 'Range') return (b.rangePct ?? -1) - (a.rangePct ?? -1);
    return a.name.localeCompare(b.name);
  });

  /** Format a nullable numeric cell, or an em-dash when evidence is absent. */
  const fmt = (value: number | null, p: DisplayRow): string =>
    value === null || value === undefined || Number.isNaN(value) ? '—' : value.toFixed(p.decimals ?? 2);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Active Watchlist Selector */}
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
        {assetClasses.map((cat) => (
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
          onChange={(e) => setSortBy(e.target.value)}
          style={{ padding: '2px 8px', fontSize: '11px' }}
        >
          <option value="Volume">Sort by Volume</option>
          <option value="Change">Sort by Change %</option>
          <option value="Volatility">Sort by Volatility</option>
          <option value="ADR">Sort by ADR</option>
          <option value="Range">Sort by Range % of ADR</option>
          <option value="Name">Sort Alphabetically</option>
        </select>
      </div>

      {/* Main Markets Table */}
      <div style={{ flex: 1, overflow: 'auto' }}>
        {status === 'loading' && directory.length === 0 && (
          <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted, #718294)' }}>
            Loading quotes for the active watchlist…
          </div>
        )}
        {status === 'error' && (
          <div role="alert" style={{ padding: '8px 24px', textAlign: 'center', color: 'var(--financial-negative, #ff4975)' }}>
            {errorMsg}
          </div>
        )}
        {status === 'ready' && sortedProducts.length === 0 && (
          <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted, #718294)' }}>
            No symbols available for {selectedCategory}.
          </div>
        )}
        {directory.length > 0 && sortedProducts.length > 0 && (
        <table className="cme-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Last Price</th>
              <th>Change</th>
              <th title="Prior settled 10-session annualized rolling volatility">Volatility</th>
              <th title="Average daily range over the last 10 sessions">ADR</th>
              <th title="Today's high minus low, and how much of the ADR it has used">Range</th>
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
              const changePips =
                p.changePips === null
                  ? null
                  : `${p.changePips >= 0 ? '+' : ''}${p.changePips.toFixed(1)}`;
              const changePercent =
                p.changePercent === null
                  ? null
                  : `${p.changePercent >= 0 ? '+' : ''}${p.changePercent.toFixed(2)}%`;
              const changeCell =
                changePips === null || changePercent === null
                  ? '—'
                  : `${changePips} (${changePercent})`;
              const rangePctCell =
                p.rangePct === null ? '—' : `${p.rangePct.toFixed(0)}%`;

              return (
                <tr key={p.symbol}>
                  <td style={{ fontWeight: 600 }}>{p.name}</td>
                  <td className={priceClass}>{fmt(p.last, p)}</td>
                  <td className={priceClass}>{changeCell}</td>
                  <td style={{ fontFamily: 'var(--font-mono)' }}>
                    {p.volatility === null ? '—' : `${p.volatility.toFixed(2)}%`}
                  </td>
                  <td style={{ fontFamily: 'var(--font-mono)' }}>
                    {p.adr === null ? '—' : `${p.adr.toFixed(1)} pips`}
                  </td>
                  <td style={{ fontFamily: 'var(--font-mono)', whiteSpace: 'nowrap' }}>
                    {fmt(p.range, p)}
                    <span className={`range-pct ${(p.rangePct ?? 0) >= 100 ? 'range-extended' : ''}`}>
                      {rangePctCell}
                    </span>
                  </td>
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
                        <div
                          className="sidebar-menu-item"
                          onClick={() => {
                            addWidgetToWorkspace('optionsGrid', `${p.symbol} Options`, p.symbol);
                            setActiveMenuSymbol(null);
                          }}
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
