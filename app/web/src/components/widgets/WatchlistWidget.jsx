import React, { useState } from 'react';
import { useTradingStore } from '../../store/useTradingStore';
import { Plus, GripVertical, Check } from 'lucide-react';

export const WatchlistWidget = () => {
  const { products, openOrderTicket, submitOrder, oneClickTrading } = useTradingStore();
  const [selectedList, setSelectedList] = useState('Featured Watchlists');
  const [selectedProducts, setSelectedProducts] = useState([
    'ESU5', 'MESU5', 'NQU5', 'MNQU5', 'CLQ5', 'GCQ5', '6EU5', 'ZCZ5'
  ]);

  const toggleProduct = (symbol) => {
    if (selectedProducts.includes(symbol)) {
      setSelectedProducts(selectedProducts.filter((s) => s !== symbol));
    } else {
      setSelectedProducts([...selectedProducts, symbol]);
    }
  };

  const watchlistItems = products.filter((p) => selectedProducts.includes(p.symbol));

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Watchlist Top Header Controls */}
      <div style={{ padding: '8px 12px', background: 'var(--cme-navy-dark)', borderBottom: '1px solid var(--cme-navy-border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontWeight: 700, fontSize: '11px', color: 'var(--text-muted)' }}>WATCHLIST:</span>
          <select className="form-select" value={selectedList} onChange={(e) => setSelectedList(e.target.value)} style={{ padding: '2px 6px', fontSize: '11px' }}>
            <option value="Featured Watchlists">Featured Watchlists</option>
            <option value="My Commodity Watchlist">My Commodity Watchlist</option>
          </select>
        </div>
        <button className="btn-cme btn-primary btn-sm">
          <Plus size={12} /> CREATE NEW
        </button>
      </div>

      {/* Main Watchlist Items Table */}
      <div style={{ flex: 1, overflow: 'auto' }}>
        <table className="cme-table">
          <thead>
            <tr>
              <th style={{ width: '24px' }}></th>
              <th>Name</th>
              <th>Contract</th>
              <th>Last Price</th>
              <th>Change</th>
              <th>Open</th>
              <th>High</th>
              <th>Low</th>
              <th>Volume</th>
              <th style={{ textAlign: 'center' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {watchlistItems.map((p) => {
              const isUp = p.change > 0;
              const isDown = p.change < 0;
              const priceClass = isUp ? 'price-up' : isDown ? 'price-down' : 'price-flat';

              return (
                <tr key={p.symbol}>
                  <td style={{ color: 'var(--text-dim)', cursor: 'grab' }}>
                    <GripVertical size={14} />
                  </td>
                  <td style={{ fontWeight: 600 }}>{p.name}</td>
                  <td style={{ color: 'var(--cme-blue-bright)', fontWeight: 600 }}>{p.symbol}</td>
                  <td className={priceClass}>{p.lastPrice.toFixed(2)}</td>
                  <td className={priceClass}>
                    {isUp ? `+${p.change.toFixed(2)} (${p.changePercent.toFixed(2)}%)` : `${p.change.toFixed(2)} (${p.changePercent.toFixed(2)}%)`}
                  </td>
                  <td style={{ fontFamily: 'var(--font-mono)' }}>{p.open.toFixed(2)}</td>
                  <td style={{ fontFamily: 'var(--font-mono)' }}>{p.high.toFixed(2)}</td>
                  <td style={{ fontFamily: 'var(--font-mono)' }}>{p.low.toFixed(2)}</td>
                  <td style={{ fontFamily: 'var(--font-mono)' }}>{p.volume.toLocaleString()}</td>
                  <td style={{ textAlign: 'center' }}>
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
