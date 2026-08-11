'use client';

import React, { useEffect, useState } from 'react';
import { useTradingStore } from '../../store/useTradingStore';
import { assetClasses } from '../../mock/productsData';
import { apiClients, unwrapData, type MarketRow } from '@/clients';
import { MoreVertical, LineChart, AlignJustify, Layers } from 'lucide-react';

/**
 * Derived display row built from a real market-directory row.
 *
 * The directory endpoint returns categorized symbols with Level-1 + latest
 * D1-bar evidence. Historical ATR(14) and ADR(10) are not part of the
 * directory surface yet, so Volatility/ADR/Range are nullable and render
 * an em-dash when absent. The fields that are populated (range, rangePct)
 * are derived from today's high/low.
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
  range: number | null;
  rangePct: number | null;
  adr: number | null;
  volatility: number | null;
}

/** Map one API row into a display row with derived intraday range. */
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
    changePercent: row.change_percent,
    open: row.open,
    high,
    low,
    volume: row.volume,
    range,
    rangePct: range !== null && row.open ? (range / row.open) * 100 : null,
    adr: null,
    volatility: null,
  };
}

export const MarketsWidget: React.FC = () => {
  const [selectedCategory, setSelectedCategory] = useState<string>('Forex');
  const [sortBy, setSortBy] = useState<string>('Volume');
  const [activeMenuSymbol, setActiveMenuSymbol] = useState<string | null>(null);
  const [directory, setDirectory] = useState<DisplayRow[]>([]);
  const [status, setStatus] = useState<'loading' | 'ready' | 'error'>('loading');
  const [errorMsg, setErrorMsg] = useState('');

  const { openOrderTicket, submitOrder, oneClickTrading, addWidgetToWorkspace } = useTradingStore();

  // Fetch the categorized market directory from the configured runtime broker
  // on mount. The backend resolves the runtime broker when source_id is omitted,
  // so this widget needs no broker identity of its own.
  useEffect(() => {
    let cancelled = false;
    setStatus('loading');
    void apiClients.data
      .markets({ limit: 200 })
      .then((response) => {
        if (cancelled) return;
        const page = unwrapData(response);
        setDirectory(page.rows.map(toDisplayRow));
        setStatus('ready');
      })
      .catch(() => {
        if (cancelled) return;
        setErrorMsg('Unable to load markets from the runtime broker.');
        setStatus('error');
      });
    return () => {
      cancelled = true;
    };
  }, []);

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
        {status === 'loading' && (
          <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted, #718294)' }}>
            Loading markets from the runtime broker…
          </div>
        )}
        {status === 'error' && (
          <div style={{ padding: '24px', textAlign: 'center', color: 'var(--financial-negative, #ff4975)' }}>
            {errorMsg}
          </div>
        )}
        {status === 'ready' && sortedProducts.length === 0 && (
          <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted, #718294)' }}>
            No symbols available for {selectedCategory}.
          </div>
        )}
        {status === 'ready' && sortedProducts.length > 0 && (
        <table className="cme-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Last Price</th>
              <th>Change</th>
              <th title="ATR(14) as a percentage of last price">Volatility</th>
              <th title="Average daily range over the last 10 sessions">ADR</th>
              <th title="Today's high minus low, and how much of the ADR it has used">Range</th>
              <th>Open</th>
              <th>High</th>
              <th>Low</th>
              <th>Volume</th>
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
                  : `${isUp ? '+' : ''}${p.change.toFixed(2)} (${p.changePercent.toFixed(2)}%)`;
              const rangePctCell =
                p.rangePct === null ? '—' : `${p.rangePct.toFixed(0)}%`;
              const volumeCell =
                p.volume === null ? '—' : p.volume.toLocaleString();

              return (
                <tr key={p.symbol}>
                  <td style={{ fontWeight: 600 }}>{p.name}</td>
                  <td className={priceClass}>{fmt(p.last, p)}</td>
                  <td className={priceClass}>{changeCell}</td>
                  <td style={{ fontFamily: 'var(--font-mono)' }}>
                    {p.volatility === null ? '—' : `${p.volatility.toFixed(2)}%`}
                  </td>
                  <td style={{ fontFamily: 'var(--font-mono)' }}>{fmt(p.adr, p)}</td>
                  <td style={{ fontFamily: 'var(--font-mono)', whiteSpace: 'nowrap' }}>
                    {fmt(p.range, p)}
                    <span className={`range-pct ${(p.rangePct ?? 0) >= 100 ? 'range-extended' : ''}`}>
                      {rangePctCell}
                    </span>
                  </td>
                  <td style={{ fontFamily: 'var(--font-mono)' }}>{fmt(p.open, p)}</td>
                  <td style={{ fontFamily: 'var(--font-mono)' }}>{fmt(p.high, p)}</td>
                  <td style={{ fontFamily: 'var(--font-mono)' }}>{fmt(p.low, p)}</td>
                  <td style={{ fontFamily: 'var(--font-mono)' }}>{volumeCell}</td>
                  <td style={{ textAlign: 'center', position: 'relative' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '4px' }}>
                      <button
                        className="btn-cme btn-outline btn-sm"
                        onClick={() => {
                          if (oneClickTrading) {
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
