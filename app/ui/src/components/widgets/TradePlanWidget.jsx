import React, { useState } from 'react';
import { Save } from 'lucide-react';

export const TradePlanWidget = () => {
  const [dollarsToRisk, setDollarsToRisk] = useState('10000.0');
  const [percentToRisk, setPercentToRisk] = useState('3.0');
  const [buyingPower, setBuyingPower] = useState('3.0');
  const [decisionInput, setDecisionInput] = useState('Technical');
  const [marketTrend, setMarketTrend] = useState('Momentum');
  const [riskReward, setRiskReward] = useState('3:1');

  const handleSave = () => {
    alert('Your Trade Plan parameters have been saved successfully.');
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', padding: '16px', overflow: 'auto', background: 'var(--cme-navy-panel)' }}>
      {/* Title & Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px', borderBottom: '1px solid var(--cme-navy-border)', paddingBottom: '10px' }}>
        <div>
          <h3 style={{ color: '#fff', fontSize: '16px' }}>My Trade Plan (Practice Account)</h3>
          <p style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
            Define your risk, set your trading objectives, and follow up regularly to refine your strategy.
          </p>
        </div>

        <button className="btn-cme btn-primary" onClick={handleSave}>
          <Save size={14} /> SAVE PLAN
        </button>
      </div>

      {/* Questionnaire Form Grid */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {/* Section A: Risk Parameters */}
        <div style={{ background: 'var(--cme-navy-dark)', border: '1px solid var(--cme-navy-border)', borderRadius: 'var(--radius-md)', padding: '14px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
          <div>
            <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--cme-blue-cyan)' }}>Section A: Risk Parameters</span>
            <p style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
              Establishing your monetary boundaries is essential to maintaining perspective and trading longevity.
            </p>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <div className="form-group">
              <label className="form-label">Dollars to risk per trade ($)</label>
              <input type="text" className="form-input" value={dollarsToRisk} onChange={(e) => setDollarsToRisk(e.target.value)} />
            </div>
            <div className="form-group">
              <label className="form-label">% willing to risk per trade</label>
              <input type="text" className="form-input" value={percentToRisk} onChange={(e) => setPercentToRisk(e.target.value)} />
            </div>
            <div className="form-group">
              <label className="form-label">% buying power willing to commit per trade</label>
              <input type="text" className="form-input" value={buyingPower} onChange={(e) => setBuyingPower(e.target.value)} />
            </div>
          </div>
        </div>

        {/* Section B: Trading Decision Inputs */}
        <div style={{ background: 'var(--cme-navy-dark)', border: '1px solid var(--cme-navy-border)', borderRadius: 'var(--radius-md)', padding: '14px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
          <div>
            <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--cme-blue-cyan)' }}>Section B: Trading Decision Inputs</span>
            <p style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
              What information do you use to make a trading decision? Fundamentals or technical indicators?
            </p>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
              <input type="radio" name="decisionInput" checked={decisionInput === 'Fundamental'} onChange={() => setDecisionInput('Fundamental')} />
              <span>Fundamental</span>
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
              <input type="radio" name="decisionInput" checked={decisionInput === 'Technical'} onChange={() => setDecisionInput('Technical')} />
              <span>Technical</span>
            </label>
          </div>
        </div>

        {/* Section C: Types of Market Trends */}
        <div style={{ background: 'var(--cme-navy-dark)', border: '1px solid var(--cme-navy-border)', borderRadius: 'var(--radius-md)', padding: '14px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
          <div>
            <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--cme-blue-cyan)' }}>Section C: Types of Market Trends</span>
            <p style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
              Do you prefer going with the flow (momentum) or capturing market extremes (reversion)?
            </p>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
              <input type="radio" name="marketTrend" checked={marketTrend === 'Momentum'} onChange={() => setMarketTrend('Momentum')} />
              <span>Momentum</span>
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
              <input type="radio" name="marketTrend" checked={marketTrend === 'Contra Trend'} onChange={() => setMarketTrend('Contra Trend')} />
              <span>Contra Trend</span>
            </label>
          </div>
        </div>

        {/* Section D: Risk Reward Ratio */}
        <div style={{ background: 'var(--cme-navy-dark)', border: '1px solid var(--cme-navy-border)', borderRadius: 'var(--radius-md)', padding: '14px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
          <div>
            <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--cme-blue-cyan)' }}>Section D: Risk Reward Ratio</span>
            <p style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
              Setting a base risk/reward ratio defines your preference for how much reward you expect per dollar risked.
            </p>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {['1:1', '2:1', '3:1', '4:1', '5:1'].map((ratio) => (
              <label key={ratio} style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                <input type="radio" name="riskReward" checked={riskReward === ratio} onChange={() => setRiskReward(ratio)} />
                <span>{ratio}</span>
              </label>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
