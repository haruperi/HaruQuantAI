import React, { useState } from 'react';
import { useTradingStore } from '../../store/useTradingStore';
import { assetClasses } from '../../mock/productsData';
import { MoreVertical, LineChart, AlignJustify, Layers } from 'lucide-react';

export const MarketsWidget = () => {
  const [selectedCategory, setSelectedCategory] = useState('Equity Index');
  const [sortBy, setSortBy] = useState('Volume');
  const [activeMenuSymbol, setActiveMenuSymbol] = useState(null);

  const { products, openOrderTicket, submitOrder, oneClickTrading, addWidgetToWorkspace } = useTradingStore();

  const filteredProducts = products.filter((p) => p.assetClass === selectedCategory);

  /**
   * Derived trading metrics.
   *  volatility - ATR(14) as a percentage of last price, i.e. the typical daily
   *               move in percent, comparable across contracts of any tick size.
   *  range      - today's high minus low, live off the quote feed.
   *  rangePct   - how much of the average day is already used. Above 100% means
   *               the contract has exceeded its normal range and may be extended.
   */
  const withMetrics = filteredProducts.map((p) => {
    const range = p.high - p.low;
    const adr = p.adr10 || 0;
    return {
      ...p,
      range,
      adr,
      volatility: p.lastPrice ? (p.atr14 / p.lastPrice) * 100 : 0,
      rangePct: adr ? (range / adr) * 100 : 0
    };
  });

  const sortedProducts = [...withMetrics].sort((a, b) => {
    if (sortBy === 'Volume') return b.volume - a.volume;
    if (sortBy === 'Change') return Math.abs(b.changePercent) - Math.abs(a.changePercent);
    if (sortBy === 'Volatility') return b.volatility - a.volatility;
    // ADR and Range are absolute point values, so they are only comparable
    // within a contract - rank by percentage terms to keep the sort meaningful
    // across, say, Gold and Copper sitting in the same Metals list.
    if (sortBy === 'ADR') return b.adr / b.lastPrice - a.adr / a.lastPrice;
    if (sortBy === 'Range') return b.rangePct - a.rangePct;
    return a.name.localeCompare(b.name);
  });

  const fmt = (value, p) => value.toFixed(p.decimals ?? 2);

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
              const isUp = p.change > 0;
              const isDown = p.change < 0;
              const priceClass = isUp ? 'price-up' : isDown ? 'price-down' : 'price-flat';

              return (
                <tr key={p.symbol}>
                  <td style={{ fontWeight: 600 }}>{p.name}</td>
                  <td className={priceClass}>{fmt(p.lastPrice, p)}</td>
                  <td className={priceClass}>
                    {isUp ? `+${p.change.toFixed(2)} (${p.changePercent.toFixed(2)}%)` : `${p.change.toFixed(2)} (${p.changePercent.toFixed(2)}%)`}
                  </td>
                  <td style={{ fontFamily: 'var(--font-mono)' }}>{p.volatility.toFixed(2)}%</td>
                  <td style={{ fontFamily: 'var(--font-mono)' }}>{fmt(p.adr, p)}</td>
                  <td style={{ fontFamily: 'var(--font-mono)', whiteSpace: 'nowrap' }}>
                    {fmt(p.range, p)}
                    <span className={`range-pct ${p.rangePct >= 100 ? 'range-extended' : ''}`}>
                      {p.rangePct.toFixed(0)}%
                    </span>
                  </td>
                  <td style={{ fontFamily: 'var(--font-mono)' }}>{fmt(p.open, p)}</td>
                  <td style={{ fontFamily: 'var(--font-mono)' }}>{fmt(p.high, p)}</td>
                  <td style={{ fontFamily: 'var(--font-mono)' }}>{fmt(p.low, p)}</td>
                  <td style={{ fontFamily: 'var(--font-mono)' }}>{p.volume.toLocaleString()}</td>
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
      </div>
    </div>
  );
};
