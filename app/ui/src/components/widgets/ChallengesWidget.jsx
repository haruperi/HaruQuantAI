import React, { useState } from 'react';
import { useTradingStore } from '../../store/useTradingStore';
import { Trophy, Users, Shield, ArrowRight } from 'lucide-react';

export const ChallengesWidget = () => {
  const { setMode } = useTradingStore();
  const [promoCode, setPromoCode] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [agreed, setAgreed] = useState(false);

  const handleJoinChallenge = () => {
    setMode('challenge');
    alert(`Successfully registered for HaruQuantAI Trading Challenge as "${displayName || 'Trader'}"! Switching to Challenge Mode.`);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', padding: '16px', background: 'var(--cme-navy-panel)', overflowY: 'auto' }}>
      {/* Top Banner Intro */}
      <div style={{ background: 'var(--cme-navy-dark)', border: '1px solid var(--cme-navy-border)', padding: '16px', borderRadius: 'var(--radius-md)', marginBottom: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h3 style={{ color: '#fff', fontSize: '15px', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Trophy color="var(--cme-warning-yellow)" size={18} /> Introduction to Challenges
          </h3>
          <p style={{ fontSize: '11px', color: 'var(--text-muted)', maxWidth: '500px', lineHeight: '1.4' }}>
            Experience trading futures and options in a realistic yet risk-free environment. Compete against peers using live market data, test your strategy, and see if you can outperform.
          </p>
        </div>

        <div style={{ textAlign: 'right', fontSize: '11px', color: 'var(--text-muted)' }}>
          <div style={{ color: 'var(--cme-blue-cyan)', fontWeight: 700 }}>KEY BENEFITS</div>
          <div>• Trade in risk-free environment</div>
          <div>• Compete with your peers</div>
        </div>
      </div>

      {/* Main Content Grid: Public vs Private Challenges */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
        {/* Public Challenges */}
        <div style={{ background: 'var(--cme-navy-dark)', border: '1px solid var(--cme-navy-border)', borderRadius: 'var(--radius-md)', padding: '14px' }}>
          <h4 style={{ color: '#fff', fontSize: '13px', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Users size={16} color="var(--cme-blue-bright)" /> Public Challenges Available
          </h4>

          <div style={{ background: 'var(--cme-navy-header)', border: '1px solid var(--cme-navy-border)', borderRadius: 'var(--radius-sm)', padding: '12px' }}>
            <div style={{ fontSize: '9px', fontWeight: 700, color: 'var(--cme-blue-cyan)', textTransform: 'uppercase' }}>PUBLIC</div>
            <h5 style={{ color: '#fff', fontSize: '13px', margin: '4px 0' }}>HaruQuantAI Public Challenge Test (July)</h5>

            <div style={{ fontSize: '10px', color: 'var(--text-muted)', margin: '8px 0', fontFamily: 'var(--font-mono)' }}>
              Start Date: 7/14/2025 12:00:00 PM CT<br />
              End Date: 8/22/2025 4:00:00 PM CT
            </div>

            <div style={{ display: 'flex', gap: '8px', marginTop: '12px' }}>
              <button className="btn-cme btn-outline btn-sm">View Details</button>
              <button className="btn-cme btn-primary btn-sm" onClick={handleJoinChallenge}>
                JOIN CHALLENGE
              </button>
            </div>
          </div>
        </div>

        {/* Private Challenges */}
        <div style={{ background: 'var(--cme-navy-dark)', border: '1px solid var(--cme-navy-border)', borderRadius: 'var(--radius-md)', padding: '14px' }}>
          <h4 style={{ color: '#fff', fontSize: '13px', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Shield size={16} color="var(--cme-blue-bright)" /> Join Private Challenge
          </h4>

          <div className="form-group" style={{ marginBottom: '10px' }}>
            <label className="form-label">Enter Promo Code</label>
            <input
              type="text"
              className="form-input"
              placeholder="Enter your promo code here"
              value={promoCode}
              onChange={(e) => setPromoCode(e.target.value)}
            />
          </div>

          <div className="form-group" style={{ marginBottom: '10px' }}>
            <label className="form-label">Display Name</label>
            <input
              type="text"
              className="form-input"
              placeholder="Your Leaderboard Display Name"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
            />
          </div>

          <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '11px', color: 'var(--text-muted)', marginBottom: '12px', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={agreed}
              onChange={(e) => setAgreed(e.target.checked)}
            />
            <span>I have read and agree to the Trading Simulator User Agreements</span>
          </label>

          <button
            className="btn-cme btn-primary"
            disabled={!agreed || !promoCode}
            onClick={handleJoinChallenge}
            style={{ width: '100%' }}
          >
            SUBMIT & JOIN <ArrowRight size={14} />
          </button>
        </div>
      </div>
    </div>
  );
};
