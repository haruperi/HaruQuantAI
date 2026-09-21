import React from 'react';
import { Award, CheckSquare, ShieldCheck, X } from 'lucide-react';
import type { BuilderSettings } from '../../app/types';
import { Button, Checkbox, Field, Section, Select, TextInput } from '../../components/ui';

interface RankingSettingsViewProps {
  isOpen: boolean;
  onClose: () => void;
  settings: BuilderSettings;
  updateSettings: (patch: Partial<BuilderSettings>) => void;
}

export const RankingSettingsView: React.FC<RankingSettingsViewProps> = ({
  isOpen,
  onClose,
  settings,
  updateSettings,
}) => {
  if (!isOpen) return null;

  const handleCrossCheckToggle = (id: string, current: boolean) => {
    const next = settings.crossChecks.map((item) =>
      item.id === id ? { ...item, enabled: !current } : item
    );
    updateSettings({ crossChecks: next });
  };

  return (
    <div className="modal-backdrop" role="dialog" aria-modal="true">
      <div className="modal-window ranking-modal-dialog" style={{ maxWidth: 760, width: '90%', maxHeight: '88vh', display: 'flex', flexDirection: 'column' }}>
        <div className="modal-header">
          <div>
            <h3>Rankings, Fitness & Cross-Check Qualification</h3>
            <span className="subtitle">Configure fitness scoring objective, dismissal thresholds, and multi-stage verification checks</span>
          </div>
          <button className="icon-button" onClick={onClose} aria-label="Close dialog">
            <X size={18} />
          </button>
        </div>

        <div style={{ flex: 1, overflowY: 'auto', padding: '18px 24px', display: 'flex', flexDirection: 'column', gap: 18 }}>
          {/* Fitness Function */}
          <Section title="Fitness Objective Function" description="Primary metric used to score and rank candidates during genetic evolution.">
            <div className="form-grid">
              <Field label="Primary Objective">
                <Select
                  value={settings.rankingMetric}
                  onChange={(val) => updateSettings({ rankingMetric: val })}
                >
                  <option>Return / Drawdown ratio</option>
                  <option>Net profit</option>
                  <option>Profit factor</option>
                  <option>Sharpe ratio</option>
                  <option>System Quality Number (SQN)</option>
                  <option>Ulcer Index</option>
                </Select>
              </Field>
            </div>
          </Section>

          {/* Automatic Dismissal Rules */}
          <Section title="Automatic Qualification & Dismissal" description="Strategies failing ANY of these criteria are rejected before entering databank.">
            <div className="form-grid">
              <Field label="Min Return / DD ratio">
                <TextInput
                  type="number"
                  step={0.1}
                  value={settings.minReturnDD}
                  onChange={(e) => updateSettings({ minReturnDD: Number(e.target.value) })}
                />
              </Field>
              <Field label="Min # of Trades">
                <TextInput
                  type="number"
                  value={settings.minTrades}
                  min={10}
                  onChange={(e) => updateSettings({ minTrades: Number(e.target.value) })}
                />
              </Field>
              <Field label="Min Profit Factor">
                <TextInput
                  type="number"
                  step={0.05}
                  value={settings.minProfitFactor}
                  onChange={(e) => updateSettings({ minProfitFactor: Number(e.target.value) })}
                />
              </Field>
              <Field label="Max Drawdown (%)">
                <TextInput
                  type="number"
                  value={settings.maxDrawdownPct}
                  min={5}
                  max={90}
                  onChange={(e) => updateSettings({ maxDrawdownPct: Number(e.target.value) })}
                />
              </Field>
              <Field label="Min Sharpe Ratio">
                <TextInput
                  type="number"
                  step={0.1}
                  value={settings.minSharpe}
                  onChange={(e) => updateSettings({ minSharpe: Number(e.target.value) })}
                />
              </Field>
            </div>
          </Section>

          {/* Multi-stage Cross-Checks */}
          <Section title="Robustness Cross-Checks Pipeline" description="Multi-stage verification tests evaluated for candidate strategies.">
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 10 }}>
              {settings.crossChecks.map((check) => (
                <label
                  key={check.id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '10px 14px',
                    borderRadius: 6,
                    border: check.enabled ? '1px solid rgba(48, 183, 232, 0.4)' : '1px solid var(--border)',
                    background: check.enabled ? 'rgba(48, 183, 232, 0.04)' : 'var(--bg-card)',
                    cursor: 'pointer',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <input
                      type="checkbox"
                      checked={check.enabled}
                      onChange={() => handleCrossCheckToggle(check.id, check.enabled)}
                      style={{ accentColor: 'var(--accent)', cursor: 'pointer' }}
                    />
                    <span style={{ fontSize: '0.86rem', fontWeight: check.enabled ? 600 : 400 }}>
                      {check.name}
                    </span>
                  </div>
                  <span
                    style={{
                      fontSize: '0.72rem',
                      padding: '2px 8px',
                      borderRadius: 10,
                      background: check.enabled ? 'rgba(74, 222, 128, 0.15)' : 'var(--bg-secondary)',
                      color: check.enabled ? '#4ade80' : 'var(--muted)',
                      fontWeight: 600,
                    }}
                  >
                    {check.enabled ? 'Active' : 'Off'}
                  </span>
                </label>
              ))}
            </div>
          </Section>
        </div>

        <div className="modal-actions" style={{ borderTop: '1px solid var(--border)', padding: '12px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--muted)' }}>
            Qualification thresholds are evaluated immediately after backtest simulation.
          </span>
          <Button className="primary" onClick={onClose}>
            Apply Ranking Rules
          </Button>
        </div>
      </div>
    </div>
  );
};
