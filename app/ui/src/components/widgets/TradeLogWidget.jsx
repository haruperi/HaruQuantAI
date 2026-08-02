import React, { useState } from 'react';
import { useTradingStore } from '../../store/useTradingStore';
import { Download, Edit3, MessageSquare } from 'lucide-react';

export const TradeLogWidget = () => {
  const { tradeLog } = useTradingStore();
  const [selectedProduct, setSelectedProduct] = useState('All Products');
  const [editingNoteId, setEditingNoteId] = useState(null);
  const [noteText, setNoteText] = useState('');

  const handleEditNote = (trade) => {
    setEditingNoteId(trade.id);
    setNoteText(trade.notes || '');
  };

  const handleSaveNote = (tradeId) => {
    // Save note in local store state
    const trade = tradeLog.find((t) => t.id === tradeId);
    if (trade) trade.notes = noteText;
    setEditingNoteId(null);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', padding: '12px', background: 'var(--cme-navy-panel)' }}>
      {/* Banner Box */}
      <div style={{ background: 'var(--cme-navy-dark)', border: '1px solid var(--cme-navy-border)', padding: '12px', borderRadius: 'var(--radius-md)', marginBottom: '12px' }}>
        <h4 style={{ color: 'var(--cme-blue-cyan)', marginBottom: '4px' }}>PRACTICE SIMULATOR TRADE LOG</h4>
        <p style={{ fontSize: '11px', color: 'var(--text-muted)', lineHeight: '1.4' }}>
          If your goal is to make money trading futures over the long haul, then embrace what the Trade Log offers—an easy, simple-to-review written record of each round-turn trade you make that will help you gauge how your choices affect your trading performance.
        </p>
      </div>

      {/* Toolbar Filters */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
        <div style={{ display: 'flex', gap: '8px' }}>
          <select className="form-select" style={{ padding: '4px 10px', fontSize: '11px' }}>
            <option>All Months</option>
          </select>
          <select className="form-select" value={selectedProduct} onChange={(e) => setSelectedProduct(e.target.value)} style={{ padding: '4px 10px', fontSize: '11px' }}>
            <option value="All Products">All Products</option>
            <option value="MNQU5">MNQU5</option>
            <option value="ESU5">ESU5</option>
          </select>
        </div>

        <button className="btn-cme btn-outline btn-sm">
          <Download size={12} /> Download CSV
        </button>
      </div>

      {/* Trade Log Table */}
      <div style={{ flex: 1, overflow: 'auto' }}>
        <table className="cme-table">
          <thead>
            <tr>
              <th>Transaction Date & Time</th>
              <th>Open/Close</th>
              <th>Buy/Sell</th>
              <th>C/P</th>
              <th>Strike Px</th>
              <th>Qty</th>
              <th>Type</th>
              <th>Px</th>
              <th>TIF</th>
              <th>Fill Px</th>
              <th>Stop Px</th>
              <th>Notes</th>
              <th style={{ textAlign: 'center' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {tradeLog.map((t) => (
              <tr key={t.id}>
                <td style={{ fontFamily: 'var(--font-mono)' }}>{t.transactionDate}</td>
                <td>{t.openClose}</td>
                <td style={{ fontWeight: 700, color: t.side === 'BUY' ? 'var(--cme-buy-green)' : 'var(--cme-sell-red)' }}>
                  {t.side}
                </td>
                <td>{t.cp}</td>
                <td>{t.strike}</td>
                <td style={{ fontFamily: 'var(--font-mono)' }}>{t.qty}</td>
                <td>{t.type}</td>
                <td style={{ fontFamily: 'var(--font-mono)' }}>{t.px}</td>
                <td>{t.tif}</td>
                <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{t.fillPx}</td>
                <td style={{ fontFamily: 'var(--font-mono)' }}>{t.stopPx}</td>
                <td style={{ color: 'var(--text-muted)', fontStyle: 'italic', maxWidth: '200px', whiteSpace: 'normal' }}>
                  {editingNoteId === t.id ? (
                    <input
                      type="text"
                      className="form-input"
                      value={noteText}
                      onChange={(e) => setNoteText(e.target.value)}
                      onBlur={() => handleSaveNote(t.id)}
                      autoFocus
                    />
                  ) : (
                    t.notes || 'No notes'
                  )}
                </td>
                <td style={{ textAlign: 'center' }}>
                  <button className="btn-cme btn-outline btn-sm" onClick={() => handleEditNote(t)}>
                    <Edit3 size={12} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
