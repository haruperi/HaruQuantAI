import React, { useState } from 'react';
import { useTradingStore } from '../../store/useTradingStore';
import { Target, X, Plus, Minus } from 'lucide-react';

export const PriceLadderWidget = ({ symbol = 'ESU5' }) => {
  const {
    products,
    oneClickTrading,
    openOrderTicket,
    submitOrder,
    flattenPositions,
    cancelAllOrders,
    positions
  } = useTradingStore();

  const targetProduct = products.find((p) => p.symbol === symbol) || products[0];
  const [orderQty, setOrderQty] = useState(1);
  const [tif, setTif] = useState('DAY');

  const currentPos = positions.find((p) => p.symbol === symbol);
  const posCount = currentPos ? currentPos.position : 'Position 0';

  // Generate ladder ticks around lastPrice
  const lastPx = targetProduct.lastPrice;
  const baseTick = Math.round(lastPx * 4) / 4;
  const ticks = [];

  for (let i = 10; i >= -10; i--) {
    const px = parseFloat((baseTick + i * 0.25).toFixed(2));
    const isLast = px === baseTick;
    const isBidSide = px <= baseTick;

    // Depth sizes
    const bidVol = isBidSide ? Math.floor(Math.abs(Math.sin(px) * 100)) + 15 : null;
    const askVol = !isBidSide ? Math.floor(Math.abs(Math.cos(px) * 100)) + 15 : null;

    ticks.push({ price: px, isLast, isBidSide, bidVol, askVol });
  }

  const handleCellClick = (side, price) => {
    if (oneClickTrading) {
      submitOrder({
        symbol: targetProduct.symbol,
        side,
        qty: orderQty,
        orderType: 'Limit',
        limitPrice: price,
        tif
      });
    } else {
      openOrderTicket({
        symbol: targetProduct.symbol,
        side,
        type: 'Limit',
        limitPrice: price
      });
    }
  };

  const handleMarketOrder = (side) => {
    if (oneClickTrading) {
      submitOrder({
        symbol: targetProduct.symbol,
        side,
        qty: orderQty,
        orderType: 'Market',
        tif
      });
    } else {
      openOrderTicket({
        symbol: targetProduct.symbol,
        side,
        type: 'Market'
      });
    }
  };

  return (
    <div className="price-ladder-container">
      {/* Top Header & Position Info */}
      <div style={{ padding: '6px 8px', background: 'var(--cme-navy-dark)', borderBottom: '1px solid var(--cme-navy-border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span style={{ fontWeight: 700, color: 'var(--cme-blue-cyan)' }}>{symbol} DOM</span>
        <span style={{ fontSize: '11px', color: 'var(--text-muted)', background: 'var(--cme-navy-header)', padding: '2px 8px', borderRadius: 'var(--radius-sm)' }}>
          {posCount}
        </span>
      </div>

      {/* Control Buttons Bar */}
      <div className="ladder-header-controls">
        <div style={{ display: 'flex', gap: '4px' }}>
          <button
            className={`btn-cme btn-outline btn-sm ${tif === 'DAY' ? 'active' : ''}`}
            onClick={() => setTif('DAY')}
            style={{ flex: 1 }}
          >
            DAY
          </button>
          <button
            className={`btn-cme btn-outline btn-sm ${tif === 'GTC' ? 'active' : ''}`}
            onClick={() => setTif('GTC')}
            style={{ flex: 1 }}
          >
            GTC
          </button>
          <button className="btn-cme btn-outline btn-sm" onClick={flattenPositions} style={{ flex: 1, color: 'var(--cme-warning-yellow)' }}>
            FLATTEN
          </button>
          <button className="btn-cme btn-outline btn-sm" onClick={cancelAllOrders} style={{ flex: 1, color: 'var(--cme-sell-red)' }}>
            CANCEL ALL
          </button>
        </div>

        {/* Quick Market Order Buttons + Qty Stepper */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <button className="btn-cme btn-buy btn-sm" onClick={() => handleMarketOrder('BUY')} style={{ flex: 1 }}>
            BUY MKT
          </button>

          <div style={{ display: 'flex', alignItems: 'center', background: 'var(--cme-navy-darkest)', border: '1px solid var(--cme-navy-border)', borderRadius: 'var(--radius-sm)' }}>
            <button className="btn-cme btn-outline btn-sm" onClick={() => setOrderQty(Math.max(1, orderQty - 1))} style={{ border: 'none' }}>
              <Minus size={10} />
            </button>
            <span style={{ fontFamily: 'var(--font-mono)', padding: '0 8px', fontWeight: 700 }}>{orderQty}</span>
            <button className="btn-cme btn-outline btn-sm" onClick={() => setOrderQty(orderQty + 1)} style={{ border: 'none' }}>
              <Plus size={10} />
            </button>
          </div>

          <button className="btn-cme btn-sell btn-sm" onClick={() => handleMarketOrder('SELL')} style={{ flex: 1 }}>
            SELL MKT
          </button>
        </div>

        {/* Quote Banner */}
        <div className="ladder-quote-banner">
          <span>BID: <b>{targetProduct.bid.toFixed(2)}</b></span>
          <span>ASK: <b>{targetProduct.ask.toFixed(2)}</b></span>
          <span>LAST: <b>{targetProduct.lastPrice.toFixed(2)}</b></span>
        </div>
      </div>

      {/* Ladder Depth Table */}
      <div style={{ flex: 1, overflowY: 'auto' }}>
        <table className="ladder-table">
          <thead>
            <tr>
              <th style={{ width: '18%' }}>QTY</th>
              <th style={{ width: '27%' }}>BUY</th>
              <th style={{ width: '28%' }}>PRICE</th>
              <th style={{ width: '27%' }}>SELL</th>
              <th style={{ width: '18%' }}>QTY</th>
            </tr>
          </thead>
          <tbody>
            {ticks.map((t) => (
              <tr key={t.price}>
                {/* Working Buy Orders Qty */}
                <td className="ladder-cell"></td>

                {/* Bid Depth Cell */}
                <td className="ladder-cell bid-depth-cell" onClick={() => handleCellClick('BUY', t.price)}>
                  {t.bidVol && (
                    <>
                      <div className="depth-bar-bid" style={{ width: `${Math.min(100, (t.bidVol / 120) * 100)}%` }} />
                      <span className="cell-content">{t.bidVol}</span>
                    </>
                  )}
                </td>

                {/* Price Cell */}
                <td className={`ladder-cell ladder-price-cell ${t.isLast ? 'last-price' : ''}`}>
                  {t.price.toFixed(2)}
                </td>

                {/* Ask Depth Cell */}
                <td className="ladder-cell ask-depth-cell" onClick={() => handleCellClick('SELL', t.price)}>
                  {t.askVol && (
                    <>
                      <div className="depth-bar-ask" style={{ width: `${Math.min(100, (t.askVol / 120) * 100)}%` }} />
                      <span className="cell-content">{t.askVol}</span>
                    </>
                  )}
                </td>

                {/* Working Sell Orders Qty */}
                <td className="ladder-cell"></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Ladder Bottom Controls */}
      <div style={{ padding: '6px', background: 'var(--cme-navy-dark)', borderTop: '1px solid var(--cme-navy-border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <button className="btn-cme btn-outline btn-sm" onClick={cancelAllOrders} title="Cancel All Working Orders">
          <X size={12} />
        </button>
        <button className="btn-cme btn-outline btn-sm" title="Re-Center Price Ladder (Spacebar)">
          <Target size={14} color="var(--cme-blue-cyan)" />
        </button>
        <button className="btn-cme btn-outline btn-sm" onClick={cancelAllOrders} title="Cancel All">
          <X size={12} color="var(--cme-sell-red)" />
        </button>
      </div>
    </div>
  );
};
