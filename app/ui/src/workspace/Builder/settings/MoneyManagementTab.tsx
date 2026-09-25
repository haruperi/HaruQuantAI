import { useState } from 'react';
import { SqdFieldset, SqdSpinner } from './SettingsControls';
import { moneyManagementDefaults, type MmMethod } from './settingsFixtures';

/** "Money management" tab (donor evidence SQX144-EV-000041). */
export function MoneyManagementTab() {
  const [initialCapital, setInitialCapital] = useState(moneyManagementDefaults.initialCapital);
  const [methods, setMethods] = useState<MmMethod[]>(moneyManagementDefaults.methods);

  const patch = (key: string, part: Partial<MmMethod>) =>
    setMethods(current => current.map(m => (m.key === key ? { ...m, ...part } : m)));

  return (
    <div className="money-management sqd-tab-content">
      <SqdFieldset legend="Choose initial capital">
        <div className="sqd-inline-controls">
          <label className="sqd-label">Initial capital</label>
          <SqdSpinner ariaLabel="Initial capital" value={initialCapital} min={0} step={100} onChange={setInitialCapital} />
        </div>
      </SqdFieldset>

      <SqdFieldset legend="Choose Money Management method">
        <div className="sqd-mm-grid" role="table" aria-label="Money management methods">
          {methods.map(method => (
            <div className={`sqd-mm-row${method.use ? ' active' : ''}`} role="row" key={method.key}>
              <label className="sqd-mm-select" role="cell">
                <input
                  type="radio"
                  name="mmMethod"
                  checked={method.use}
                  onChange={() => setMethods(current => current.map(m => ({ ...m, use: m.key === method.key })))}
                />
                <span className="sqd-mark" />
                {method.label}
              </label>
              <div className="sqd-mm-params" role="cell">
                {method.params.map(param => (
                  <span className="sqd-mm-param" key={param.key}>
                    <label className="sqd-label">{param.label}</label>
                    <input className="sqd-input sqd-mm-value" aria-label={`${method.label} ${param.label}`} value={param.value} disabled={!method.use} onChange={e => patch(method.key, { params: method.params.map(p => p.key === param.key ? {...p, value:e.target.value} : p) })} />
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </SqdFieldset>
    </div>
  );
}
