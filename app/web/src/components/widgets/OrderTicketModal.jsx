import React, { useState, useEffect } from 'react';
import { useTradingStore } from '../../store/useTradingStore';
import { X, Plus, Minus } from 'lucide-react';

export const OrderTicketModal = () => {
  const {
    isOrderTicketOpen,
    closeOrderTicket,
    orderTicketProps,
    products,
    submitOrder
  } = useTradingStore();

  const [activeTab, setActiveTab] = useState('futures');
  const [side, setSide] = useState('BUY');
  const [orderType, setOrderType] = useState('Market');
  const [quantity, setQuantity] = useState(1);
  const [tif, setTif] = useState('DAY');
  const [limitPrice, setLimitPrice] = useState('');
  const [stopPrice, setStopPrice] = useState('');

  // Options fields
  const [optionType, setOptionType] = useState('CALL');
  const [strikePrice, setStrikePrice] = useState('61000');

  const initialSymbol = orderTicketProps?.symbol || 'ESU5';
  const targetProduct = products.find((p) => p.symbol === initialSymbol) || products[0] || { symbol: 'ESU5', lastPrice: 6244.00, bid: 6243.75, ask: 6244.25, volume: 1000, change: 0 };

  useEffect(() => {
    if (isOrderTicketOpen && orderTicketProps) {
      if (orderTicketProps.defaultTab) setActiveTab(orderTicketProps.defaultTab);
      if (orderTicketProps.side) setSide(orderTicketProps.side);
      if (orderTicketProps.type) setOrderType(orderTicketProps.type);
      if (orderTicketProps.limitPrice) setLimitPrice(orderTicketProps.limitPrice);
      else setLimitPrice(targetProduct.lastPrice);
      setStopPrice(targetProduct.lastPrice - 5);
      if (orderTicketProps.cp) setOptionType(orderTicketProps.cp);
      if (orderTicketProps.strike) setStrikePrice(orderTicketProps.strike);
    }
  }, [isOrderTicketOpen, orderTicketProps, targetProduct.lastPrice]);

  if (!isOrderTicketOpen) return null;

  const isBuy = side === 'BUY';

  const handleSubmit = (e) => {
    e.preventDefault();
    submitOrder({
      symbol: targetProduct.symbol,
      side,
      qty: quantity,
      orderType,
      limitPrice: Number(limitPrice),
      stopPrice: Number(stopPrice),
      tif,
      cp: activeTab === 'options' ? optionType : '-',
      strike: activeTab === 'options' ? strikePrice : '-'
    });
  };

  return (
    <div className="modal-overlay" onClick={closeOrderTicket}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        {/* Modal Header */}
        <div className="modal-header">
          <span>Trade - {targetProduct.symbol}</span>
          <button className="widget-btn" onClick={closeOrderTicket}>
            <X size={16} />
          </button>
        </div>

        {/* Live Quote Header Banner */}
        <div style={{ padding: '8px 16px', background: 'var(--cme-navy-dark)', borderBottom: '1px solid var(--cme-navy-border)', display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', textAlign: 'center', fontSize: '11px', fontFamily: 'var(--font-mono)' }}>
          <div>
            <div style={{ color: 'var(--text-muted)', fontSize: '9px' }}>BID</div>
            <div style={{ fontWeight: 600 }}>{targetProduct.bid.toFixed(2)}</div>
          </div>
          <div>
            <div style={{ color: 'var(--text-muted)', fontSize: '9px' }}>ASK</div>
            <div style={{ fontWeight: 600 }}>{targetProduct.ask.toFixed(2)}</div>
          </div>
          <div>
            <div style={{ color: 'var(--text-muted)', fontSize: '9px' }}>LAST</div>
            <div style={{ fontWeight: 600, color: 'var(--cme-blue-cyan)' }}>{targetProduct.lastPrice.toFixed(2)}</div>
          </div>
          <div>
            <div style={{ color: 'var(--text-muted)', fontSize: '9px' }}>VOLUME</div>
            <div style={{ fontWeight: 600 }}>{targetProduct.volume.toLocaleString()}</div>
          </div>
          <div>
            <div style={{ color: 'var(--text-muted)', fontSize: '9px' }}>CHANGE</div>
            <div className={targetProduct.change >= 0 ? 'price-up' : 'price-down'} style={{ fontWeight: 600 }}>
              {targetProduct.change >= 0 ? `+${targetProduct.change.toFixed(2)}` : targetProduct.change.toFixed(2)}
            </div>
          </div>
        </div>

        {/* Futures / Options Tab Switcher */}
        <div style={{ display: 'flex', borderBottom: '1px solid var(--cme-navy-border)', background: 'var(--cme-navy-header)' }}>
          <button
            className={`toggle-option ${activeTab === 'futures' ? 'active default' : ''}`}
            onClick={() => setActiveTab('futures')}
            style={{ borderRadius: 0 }}
          >
            Futures
          </button>
          <button
            className={`toggle-option ${activeTab === 'options' ? 'active default' : ''}`}
            onClick={() => setActiveTab('options')}
            style={{ borderRadius: 0 }}
          >
            Options
          </button>
        </div>

        {/* Modal Form Body */}
        <form onSubmit={handleSubmit} className="modal-body">
          {/* Side & Quantity Selector */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div className="form-group">
              <label className="form-label">Side</label>
              <div className="toggle-group">
                <div
                  className={`toggle-option ${side === 'BUY' ? 'active buy' : ''}`}
                  onClick={() => setSide('BUY')}
                >
                  BUY
                </div>
                <div
                  className={`toggle-option ${side === 'SELL' ? 'active sell' : ''}`}
                  onClick={() => setSide('SELL')}
                >
                  SELL
                </div>
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Quantity (1-10)</label>
              <div style={{ display: 'flex', alignItems: 'center', background: 'var(--cme-navy-darkest)', border: '1px solid var(--cme-navy-border)', borderRadius: 'var(--radius-sm)' }}>
                <button type="button" className="btn-cme btn-outline" onClick={() => setQuantity(Math.max(1, quantity - 1))} style={{ padding: '6px 10px', border: 'none' }}>
                  <Minus size={12} />
                </button>
                <input
                  type="number"
                  value={quantity}
                  onChange={(e) => setQuantity(Number(e.target.value))}
                  style={{ width: '100%', textAlign: 'center', background: 'transparent', border: 'none', color: '#fff', fontFamily: 'var(--font-mono)', fontWeight: 600 }}
                />
                <button type="button" className="btn-cme btn-outline" onClick={() => setQuantity(quantity + 1)} style={{ padding: '6px 10px', border: 'none' }}>
                  <Plus size={12} />
                </button>
              </div>
            </div>
          </div>

          {/* Time In Force & Order Type */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div className="form-group">
              <label className="form-label">Time-in-force</label>
              <div className="toggle-group">
                <div
                  className={`toggle-option ${tif === 'DAY' ? 'active default' : ''}`}
                  onClick={() => setTif('DAY')}
                >
                  DAY
                </div>
                <div
                  className={`toggle-option ${tif === 'GTC' ? 'active default' : ''}`}
                  onClick={() => setTif('GTC')}
                >
                  GTC
                </div>
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Order Type</label>
              <select className="form-select" value={orderType} onChange={(e) => setOrderType(e.target.value)}>
                <option value="Market">Market</option>
                <option value="Limit">Limit</option>
                <option value="Stop">Stop</option>
                <option value="Stop Limit">Stop Limit</option>
              </select>
            </div>
          </div>

          {/* Limit Price & Stop Price Fields */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div className="form-group">
              <label className="form-label">Limit Price</label>
              <input
                type="number"
                step="0.25"
                className="form-input"
                value={limitPrice}
                disabled={orderType === 'Market' || orderType === 'Stop'}
                onChange={(e) => setLimitPrice(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Stop Price</label>
              <input
                type="number"
                step="0.25"
                className="form-input"
                value={stopPrice}
                disabled={orderType === 'Market' || orderType === 'Limit'}
                onChange={(e) => setStopPrice(e.target.value)}
              />
            </div>
          </div>

          {/* Options Specific Controls (when Options Tab Active) */}
          {activeTab === 'options' && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', background: 'var(--cme-navy-dark)', padding: '10px', borderRadius: 'var(--radius-md)', border: '1px solid var(--cme-navy-border)' }}>
              <div className="form-group">
                <label className="form-label">Put / Call</label>
                <div className="toggle-group">
                  <div
                    className={`toggle-option ${optionType === 'PUT' ? 'active default' : ''}`}
                    onClick={() => setOptionType('PUT')}
                  >
                    PUT
                  </div>
                  <div
                    className={`toggle-option ${optionType === 'CALL' ? 'active default' : ''}`}
                    onClick={() => setOptionType('CALL')}
                  >
                    CALL
                  </div>
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Strike Price</label>
                <select className="form-select" value={strikePrice} onChange={(e) => setStrikePrice(e.target.value)}>
                  <option value="60500">60500</option>
                  <option value="60750">60750</option>
                  <option value="61000">61000 (ATM)</option>
                  <option value="61250">61250</option>
                  <option value="61500">61500</option>
                </select>
              </div>
            </div>
          )}

          {/* Submit Action Button */}
          <button
            type="submit"
            className={`btn-cme ${isBuy ? 'btn-buy' : 'btn-sell'}`}
            style={{ width: '100%', padding: '10px', fontSize: '14px', fontWeight: 700, marginTop: '8px' }}
          >
            {isBuy ? `BUY ${quantity} ${targetProduct.symbol}` : `SELL ${quantity} ${targetProduct.symbol}`}
          </button>
        </form>
      </div>
    </div>
  );
};
