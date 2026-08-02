import React, { useState } from 'react';
import { useTradingStore } from '../../store/useTradingStore';
import { generateOptionsGrid } from '../../mock/optionsData';
import { Plus } from 'lucide-react';

export const OptionsGridWidget = ({ symbol = 'ESU5' }) => {
  const { products, openOrderTicket, submitOrder, oneClickTrading } = useTradingStore();
  const targetProduct = products.find((p) => p.symbol === symbol) || products[0];

  const gridData = generateOptionsGrid(targetProduct.lastPrice);

  const handleCellClick = (strike, cp, side, price) => {
    if (oneClickTrading) {
      submitOrder({
        symbol: targetProduct.symbol,
        side,
        qty: 1,
        orderType: 'Limit',
        limitPrice: price,
        cp,
        strike: strike.toString()
      });
    } else {
      openOrderTicket({
        symbol: targetProduct.symbol,
        side,
        type: 'Limit',
        limitPrice: price,
        defaultTab: 'options',
        cp,
        strike: strike.toString()
      });
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Options Header Metrics Bar */}
      <div style={{ padding: '8px 12px', background: 'var(--cme-navy-dark)', borderBottom: '1px solid var(--cme-navy-border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '11px', flexWrap: 'wrap', gap: '10px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontWeight: 700, color: 'var(--text-muted)' }}>UNDERLYING FUTURE:</span>
          <span style={{ fontWeight: 700, color: 'var(--cme-blue-cyan)' }}>{targetProduct.name} ({targetProduct.symbol})</span>
        </div>

        <div style={{ display: 'flex', gap: '14px', fontFamily: 'var(--font-mono)' }}>
          <span>LAST: <b>{targetProduct.lastPrice.toFixed(2)}</b></span>
          <span className={targetProduct.change >= 0 ? 'price-up' : 'price-down'}>
            CHANGE: <b>{targetProduct.change >= 0 ? `+${targetProduct.change.toFixed(2)}` : targetProduct.change.toFixed(2)}</b>
          </span>
          <span>SETTLE: <b>{targetProduct.priorSettle.toFixed(2)}</b></span>
          <span>HIGH: <b>{targetProduct.high.toFixed(2)}</b></span>
          <span>LOW: <b>{targetProduct.low.toFixed(2)}</b></span>
          <span>VOLUME: <b>{targetProduct.volume.toLocaleString()}</b></span>
        </div>
      </div>

      {/* Main Dual Options Grid Table */}
      <div style={{ flex: 1, overflow: 'auto' }}>
        <table className="cme-table" style={{ fontSize: '11px', textAlign: 'center' }}>
          <thead>
            <tr>
              <th colSpan="8" style={{ background: '#0f2647', color: 'var(--cme-blue-bright)', textAlign: 'center', borderRight: '1px solid var(--cme-navy-border)' }}>CALLS</th>
              <th style={{ background: 'var(--cme-navy-header)', textAlign: 'center' }}>STRIKE</th>
              <th colSpan="8" style={{ background: '#0f2647', color: 'var(--cme-blue-bright)', textAlign: 'center', borderLeft: '1px solid var(--cme-navy-border)' }}>PUTS</th>
            </tr>
            <tr>
              <th>LOW</th>
              <th>HIGH</th>
              <th>PRIOR</th>
              <th>CHNGE</th>
              <th>LAST</th>
              <th>QTY</th>
              <th style={{ background: 'rgba(0, 184, 148, 0.15)', color: 'var(--cme-buy-green)' }}>BID</th>
              <th style={{ background: 'rgba(239, 83, 80, 0.15)', color: 'var(--cme-sell-red)' }}>OFFER</th>
              <th style={{ background: 'var(--cme-navy-dark)', color: '#fff' }}>PRICE</th>
              <th style={{ background: 'rgba(0, 184, 148, 0.15)', color: 'var(--cme-buy-green)' }}>BID</th>
              <th style={{ background: 'rgba(239, 83, 80, 0.15)', color: 'var(--cme-sell-red)' }}>OFFER</th>
              <th>QTY</th>
              <th>LAST</th>
              <th>CHNGE</th>
              <th>PRIOR</th>
              <th>LOW</th>
              <th>HIGH</th>
            </tr>
          </thead>
          <tbody>
            {gridData.map((row) => (
              <tr key={row.strike} style={{ background: row.isATM ? 'rgba(0, 163, 224, 0.12)' : undefined }}>
                {/* Calls Metrics */}
                <td style={{ fontFamily: 'var(--font-mono)' }}>{row.calls.low}</td>
                <td style={{ fontFamily: 'var(--font-mono)' }}>{row.calls.high}</td>
                <td style={{ fontFamily: 'var(--font-mono)' }}>{row.calls.prior}</td>
                <td className={row.calls.change >= 0 ? 'price-up' : 'price-down'}>
                  {row.calls.change >= 0 ? `+${row.calls.change}` : row.calls.change}
                </td>
                <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{row.calls.last}</td>
                <td style={{ fontFamily: 'var(--font-mono)' }}>{row.calls.qty}</td>

                {/* Call Bid / Offer Interactive Cells */}
                <td
                  className="bid-depth-cell"
                  style={{ fontFamily: 'var(--font-mono)', fontWeight: 700 }}
                  onClick={() => handleCellClick(row.strike, 'CALL', 'BUY', row.calls.bid)}
                >
                  {row.calls.bid}
                </td>
                <td
                  className="ask-depth-cell"
                  style={{ fontFamily: 'var(--font-mono)', fontWeight: 700 }}
                  onClick={() => handleCellClick(row.strike, 'CALL', 'SELL', row.calls.offer)}
                >
                  {row.calls.offer}
                </td>

                {/* Strike Center Price Column */}
                <td
                  style={{
                    fontFamily: 'var(--font-mono)',
                    fontWeight: 700,
                    background: row.isATM ? 'var(--cme-blue-primary)' : 'var(--cme-navy-header)',
                    color: '#ffffff'
                  }}
                >
                  {row.strike}
                </td>

                {/* Put Bid / Offer Interactive Cells */}
                <td
                  className="bid-depth-cell"
                  style={{ fontFamily: 'var(--font-mono)', fontWeight: 700 }}
                  onClick={() => handleCellClick(row.strike, 'PUT', 'BUY', row.puts.bid)}
                >
                  {row.puts.bid}
                </td>
                <td
                  className="ask-depth-cell"
                  style={{ fontFamily: 'var(--font-mono)', fontWeight: 700 }}
                  onClick={() => handleCellClick(row.strike, 'PUT', 'SELL', row.puts.offer)}
                >
                  {row.puts.offer}
                </td>

                {/* Puts Metrics */}
                <td style={{ fontFamily: 'var(--font-mono)' }}>{row.puts.qty}</td>
                <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{row.puts.last}</td>
                <td className={row.puts.change >= 0 ? 'price-up' : 'price-down'}>
                  {row.puts.change >= 0 ? `+${row.puts.change}` : row.puts.change}
                </td>
                <td style={{ fontFamily: 'var(--font-mono)' }}>{row.puts.prior}</td>
                <td style={{ fontFamily: 'var(--font-mono)' }}>{row.puts.low}</td>
                <td style={{ fontFamily: 'var(--font-mono)' }}>{row.puts.high}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
