import React, { useState } from 'react';
import { useTradingStore } from '../../store/useTradingStore';

export const PositionsWidget = () => {
  const [activeTab, setActiveTab] = useState('positions');
  const [posFilter, setPosFilter] = useState('All');
  const [ordFilter, setOrdFilter] = useState('All');

  const {
    positions,
    orders,
    flattenPositions,
    cancelAllOrders,
    cancelOrder,
    openOrderTicket,
    submitOrder,
    oneClickTrading
  } = useTradingStore();

  const filteredOrders = orders.filter((o) => {
    if (ordFilter === 'Working') return o.status === 'Working';
    if (ordFilter === 'Filled') return o.status === 'Filled';
    if (ordFilter === 'Cancelled') return o.status === 'Cancelled';
    return true;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Sub-header Tab Switcher */}
      <div style={{ display: 'flex', alignItems: 'center', background: 'var(--cme-navy-dark)', borderBottom: '1px solid var(--cme-navy-border)', padding: '0 8px' }}>
        <button
          className={`workspace-tab ${activeTab === 'positions' ? 'active' : ''}`}
          onClick={() => setActiveTab('positions')}
          style={{ borderRadius: 0, padding: '8px 14px' }}
        >
          Positions ({positions.length})
        </button>
        <button
          className={`workspace-tab ${activeTab === 'orders' ? 'active' : ''}`}
          onClick={() => setActiveTab('orders')}
          style={{ borderRadius: 0, padding: '8px 14px' }}
        >
          Orders ({orders.length})
        </button>
      </div>

      {/* POSITIONS TAB */}
      {activeTab === 'positions' && (
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          {/* Controls Bar */}
          <div style={{ padding: '6px 10px', background: 'var(--cme-navy-header)', borderBottom: '1px solid var(--cme-navy-border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div className="category-pills" style={{ background: 'transparent', padding: 0, border: 'none' }}>
              {['All', 'Open', 'Closed'].map((f) => (
                <div
                  key={f}
                  className={`category-pill ${posFilter === f ? 'active' : ''}`}
                  onClick={() => setPosFilter(f)}
                >
                  {f}
                </div>
              ))}
            </div>

            <button className="btn-cme btn-outline btn-sm" onClick={flattenPositions} style={{ color: 'var(--cme-warning-yellow)' }}>
              FLATTEN ALL POSITIONS
            </button>
          </div>

          {/* Positions Table */}
          <div style={{ flex: 1, overflow: 'auto' }}>
            <table className="cme-table">
              <thead>
                <tr>
                  <th>Symbol</th>
                  <th>Contract</th>
                  <th>Month</th>
                  <th>Strike</th>
                  <th>C/P</th>
                  <th>Position</th>
                  <th>Buys</th>
                  <th>Sells</th>
                  <th>Average Px</th>
                  <th>Unrealized P/L</th>
                  <th>Realized P/L</th>
                  <th style={{ textAlign: 'center' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {positions.length === 0 ? (
                  <tr>
                    <td colSpan="12" style={{ textAlign: 'center', padding: '20px', color: 'var(--text-muted)' }}>
                      No open positions to display
                    </td>
                  </tr>
                ) : (
                  positions.map((p, idx) => (
                    <tr key={idx}>
                      <td style={{ fontWeight: 700, color: 'var(--cme-blue-cyan)' }}>{p.symbol}</td>
                      <td>{p.contract}</td>
                      <td>{p.month}</td>
                      <td>{p.strike}</td>
                      <td>{p.cp}</td>
                      <td style={{ fontWeight: 600, color: p.position.includes('Long') ? 'var(--cme-buy-green)' : 'var(--cme-sell-red)' }}>
                        {p.position}
                      </td>
                      <td style={{ fontFamily: 'var(--font-mono)' }}>{p.buys}</td>
                      <td style={{ fontFamily: 'var(--font-mono)' }}>{p.sells}</td>
                      <td style={{ fontFamily: 'var(--font-mono)' }}>{p.averagePx.toFixed(2)}</td>
                      <td className={p.unrealizedPL > 0 ? 'price-up' : p.unrealizedPL < 0 ? 'price-down' : 'price-flat'}>
                        ${p.unrealizedPL.toFixed(2)}
                      </td>
                      <td className={p.realizedPL > 0 ? 'price-up' : p.realizedPL < 0 ? 'price-down' : 'price-flat'}>
                        ${p.realizedPL.toFixed(2)}
                      </td>
                      <td style={{ textAlign: 'center' }}>
                        <div style={{ display: 'flex', gap: '4px', justifyContent: 'center' }}>
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
                          <button className="btn-cme btn-sell btn-sm" onClick={flattenPositions}>
                            FLATTEN
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ORDERS TAB */}
      {activeTab === 'orders' && (
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          {/* Controls Bar */}
          <div style={{ padding: '6px 10px', background: 'var(--cme-navy-header)', borderBottom: '1px solid var(--cme-navy-border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div className="category-pills" style={{ background: 'transparent', padding: 0, border: 'none' }}>
              {['All', 'Working', 'Filled', 'Cancelled'].map((f) => (
                <div
                  key={f}
                  className={`category-pill ${ordFilter === f ? 'active' : ''}`}
                  onClick={() => setOrdFilter(f)}
                >
                  {f}
                </div>
              ))}
            </div>

            <button className="btn-cme btn-outline btn-sm" onClick={cancelAllOrders} style={{ color: 'var(--cme-sell-red)' }}>
              CANCEL ALL
            </button>
          </div>

          {/* Orders Table */}
          <div style={{ flex: 1, overflow: 'auto' }}>
            <table className="cme-table">
              <thead>
                <tr>
                  <th>Side</th>
                  <th>Symbol</th>
                  <th>Month</th>
                  <th>Strike</th>
                  <th>C/P</th>
                  <th>Qty</th>
                  <th>Leaves</th>
                  <th>Type</th>
                  <th>Fill Px</th>
                  <th>Limit Px</th>
                  <th>Stop Px</th>
                  <th>Status</th>
                  <th style={{ textAlign: 'center' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredOrders.map((o) => (
                  <tr key={o.id}>
                    <td style={{ fontWeight: 700, color: o.side === 'BUY' ? 'var(--cme-buy-green)' : 'var(--cme-sell-red)' }}>
                      {o.side}
                    </td>
                    <td style={{ fontWeight: 600 }}>{o.symbol}</td>
                    <td>{o.month}</td>
                    <td>{o.strike}</td>
                    <td>{o.cp}</td>
                    <td style={{ fontFamily: 'var(--font-mono)' }}>{o.qty}</td>
                    <td style={{ fontFamily: 'var(--font-mono)' }}>{o.leaves}</td>
                    <td>{o.type}</td>
                    <td style={{ fontFamily: 'var(--font-mono)' }}>{o.fillPx}</td>
                    <td style={{ fontFamily: 'var(--font-mono)' }}>{o.limitPx}</td>
                    <td style={{ fontFamily: 'var(--font-mono)' }}>{o.stopPx}</td>
                    <td>
                      <span
                        style={{
                          padding: '2px 6px',
                          borderRadius: 'var(--radius-sm)',
                          fontSize: '10px',
                          fontWeight: 600,
                          background: o.status === 'Working' ? 'rgba(241, 196, 15, 0.15)' : o.status === 'Filled' ? 'rgba(0, 184, 148, 0.15)' : 'rgba(239, 83, 80, 0.15)',
                          color: o.status === 'Working' ? 'var(--cme-warning-yellow)' : o.status === 'Filled' ? 'var(--cme-buy-green)' : 'var(--cme-sell-red)'
                        }}
                      >
                        {o.status}
                      </span>
                    </td>
                    <td style={{ textAlign: 'center' }}>
                      {o.status === 'Working' && (
                        <button className="btn-cme btn-outline btn-sm" onClick={() => cancelOrder(o.id)}>
                          CANCEL
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
