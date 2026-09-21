import React from 'react';
import { ShieldAlert, Sliders, X } from 'lucide-react';
import type { BuilderSettings } from '../../app/types';
import { Button, Checkbox, Field, Section, Select, TextInput } from '../../components/ui';

interface ATMConfigModalProps {
  isOpen: boolean;
  onClose: () => void;
  settings: BuilderSettings;
  updateSettings: (patch: Partial<BuilderSettings>) => void;
}

export const ATMConfigModal: React.FC<ATMConfigModalProps> = ({
  isOpen,
  onClose,
  settings,
  updateSettings,
}) => {
  if (!isOpen) return null;

  return (
    <div className="modal-backdrop" role="dialog" aria-modal="true">
      <div className="modal-window atm-modal-dialog" style={{ maxWidth: 760, width: '90%', maxHeight: '88vh', display: 'flex', flexDirection: 'column' }}>
        <div className="modal-header">
          <div>
            <h3>Money Management & Advanced Trade Management (ATM)</h3>
            <span className="subtitle">Configure position sizing, risk rules, trailing stops, and break-even protections</span>
          </div>
          <button className="icon-button" onClick={onClose} aria-label="Close dialog">
            <X size={18} />
          </button>
        </div>

        <div style={{ flex: 1, overflowY: 'auto', padding: '18px 24px', display: 'flex', flexDirection: 'column', gap: 18 }}>
          {/* Section 1: Money Management */}
          <Section title="Money Management & Capital" description="Choose risk sizing model and initial starting balance.">
            <div className="form-grid">
              <Field label="Risk Sizing Model">
                <Select
                  value={settings.mmModel}
                  onChange={(val) => updateSettings({ mmModel: val as typeof settings.mmModel })}
                >
                  <option>Fixed Size</option>
                  <option>Risk % of Equity</option>
                  <option>Risk Fixed Amount</option>
                  <option>Fixed Risk to Return</option>
                </Select>
              </Field>

              <Field label="Initial Capital ($)">
                <TextInput
                  type="number"
                  value={settings.initialCapital}
                  min={100}
                  step={1000}
                  onChange={(e) => updateSettings({ initialCapital: Number(e.target.value) })}
                />
              </Field>

              {settings.mmModel === 'Fixed Size' && (
                <Field label="Fixed Lot Size">
                  <TextInput
                    type="number"
                    value={settings.fixedLots}
                    min={0.01}
                    max={100}
                    step={0.01}
                    onChange={(e) => updateSettings({ fixedLots: Number(e.target.value) })}
                  />
                </Field>
              )}

              {settings.mmModel === 'Risk % of Equity' && (
                <Field label="Risk per Trade (%)">
                  <TextInput
                    type="number"
                    value={settings.riskPercent}
                    min={0.1}
                    max={20}
                    step={0.1}
                    onChange={(e) => updateSettings({ riskPercent: Number(e.target.value) })}
                  />
                </Field>
              )}

              {settings.mmModel === 'Risk Fixed Amount' && (
                <Field label="Max Risk per Trade ($)">
                  <TextInput
                    type="number"
                    value={250}
                    min={10}
                    step={50}
                    onChange={() => {}}
                  />
                </Field>
              )}
            </div>
          </Section>

          {/* Section 2: Stop Loss & Profit Target Modes */}
          <Section title="Stop Loss & Profit Target Rules" description="Define exit boundary ranges and calculation units.">
            <div className="form-grid">
              <Field label="Stop Loss Type">
                <Select
                  value={settings.slType}
                  onChange={(val) => updateSettings({ slType: val as typeof settings.slType })}
                >
                  <option>Fixed pips</option>
                  <option>ATR</option>
                  <option>Percent</option>
                </Select>
              </Field>

              <Field label="Profit Target Type">
                <Select
                  value={settings.ptType}
                  onChange={(val) => updateSettings({ ptType: val as typeof settings.ptType })}
                >
                  <option>Fixed pips</option>
                  <option>ATR</option>
                  <option>Percent</option>
                </Select>
              </Field>

              <Field label={`SL Minimum (${settings.slType})`}>
                <TextInput
                  type="number"
                  value={settings.slMin}
                  min={1}
                  onChange={(e) => updateSettings({ slMin: Number(e.target.value) })}
                />
              </Field>

              <Field label={`SL Maximum (${settings.slType})`}>
                <TextInput
                  type="number"
                  value={settings.slMax}
                  min={1}
                  onChange={(e) => updateSettings({ slMax: Number(e.target.value) })}
                />
              </Field>

              <Field label={`PT Minimum (${settings.ptType})`}>
                <TextInput
                  type="number"
                  value={settings.ptMin}
                  min={1}
                  onChange={(e) => updateSettings({ ptMin: Number(e.target.value) })}
                />
              </Field>

              <Field label={`PT Maximum (${settings.ptType})`}>
                <TextInput
                  type="number"
                  value={settings.ptMax}
                  min={1}
                  onChange={(e) => updateSettings({ ptMax: Number(e.target.value) })}
                />
              </Field>
            </div>
          </Section>

          {/* Section 3: Trailing Stop & Break-Even Protections */}
          <Section title="Advanced Protection (Trailing & Break-Even)" description="Dynamic stop adjustments as position moves into profit.">
            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: 12, background: 'var(--bg-card)', borderRadius: 6, border: '1px solid var(--border)' }}>
                <div>
                  <strong>Enable Trailing Stop</strong>
                  <p style={{ margin: 0, fontSize: '0.78rem', color: 'var(--muted)' }}>
                    Continuously advances stop order behind market peak to protect accumulated gains.
                  </p>
                </div>
                <Checkbox
                  label="Active"
                  checked={settings.useTrailingStop}
                  onChange={(checked) => updateSettings({ useTrailingStop: checked })}
                />
              </div>

              {settings.useTrailingStop && (
                <div className="form-grid" style={{ paddingLeft: 16 }}>
                  <Field label="Trailing Distance Min (pips)">
                    <TextInput
                      type="number"
                      value={settings.trailingStopMin}
                      min={5}
                      onChange={(e) => updateSettings({ trailingStopMin: Number(e.target.value) })}
                    />
                  </Field>
                  <Field label="Trailing Distance Max (pips)">
                    <TextInput
                      type="number"
                      value={settings.trailingStopMax}
                      min={10}
                      onChange={(e) => updateSettings({ trailingStopMax: Number(e.target.value) })}
                    />
                  </Field>
                </div>
              )}

              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: 12, background: 'var(--bg-card)', borderRadius: 6, border: '1px solid var(--border)' }}>
                <div>
                  <strong>Move Stop Loss to Break-Even</strong>
                  <p style={{ margin: 0, fontSize: '0.78rem', color: 'var(--muted)' }}>
                    Shifts stop loss to entry price (or slightly above) once a profit threshold is reached.
                  </p>
                </div>
                <Checkbox
                  label="Active"
                  checked={settings.useMoveToBE}
                  onChange={(checked) => updateSettings({ useMoveToBE: checked })}
                />
              </div>

              {settings.useMoveToBE && (
                <div className="form-grid" style={{ paddingLeft: 16 }}>
                  <Field label="Break-Even Trigger (pips)">
                    <TextInput
                      type="number"
                      value={settings.beTriggerPips}
                      min={5}
                      onChange={(e) => updateSettings({ beTriggerPips: Number(e.target.value) })}
                    />
                  </Field>
                  <Field label="Profit Offset (pips)">
                    <TextInput
                      type="number"
                      value={settings.beProfitOffset}
                      min={0}
                      onChange={(e) => updateSettings({ beProfitOffset: Number(e.target.value) })}
                    />
                  </Field>
                </div>
              )}
            </div>
          </Section>
        </div>

        <div className="modal-actions" style={{ borderTop: '1px solid var(--border)', padding: '12px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--muted)' }}>
            ATM parameters will be used when synthesizing order management rules.
          </span>
          <Button className="primary" onClick={onClose}>
            Apply Settings
          </Button>
        </div>
      </div>
    </div>
  );
};
