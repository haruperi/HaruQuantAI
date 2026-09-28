import { useState } from 'react';
import { SqdCheckbox, SqdFieldset, SqdSpinner } from './SettingsControls';
import { SqdModal } from '../ProjectModal';
import { atmDefaults, type AtmMethod } from './sharedSettingsFixtures';

/**
 * "ATM" tab (donor evidence SQX144-EV-000042): Advanced Trade Management
 * surface. The donor editor is 1,206 template lines of method/parameter
 * tables; this is the donor-style structure with the demo method set
 * derived from the exit formulas of the Build template.
 */
export function AtmTab() {
  const [adding, setAdding] = useState(false);
  const [selected, setSelected] = useState(atmDefaults[0].key);
  const [methods, setMethods] = useState<AtmMethod[]>(atmDefaults);

  const patchMethod = (key: string, part: Partial<AtmMethod>) =>
    setMethods(current => current.map(m => (m.key === key ? { ...m, ...part } : m)));

  const patchParam = (key: string, paramKey: string, value: number) =>
    setMethods(current =>
      current.map(m => (m.key === key ? { ...m, params: m.params.map(p => (p.key === paramKey ? { ...p, value } : p)) } : m)),
    );

  return (
    <div className="sqd-tab-content sqd-atm">
      <SqdFieldset legend="Advanced Trade Management">
        <p className="sqd-gen-help">
          ATM methods are applied to every generated strategy. Configure which exit methods are used and with what parameters.
        </p>
        <div className="sqd-atm-table" role="table" aria-label="ATM methods">
          <div className="sqd-atm-head" role="row">
            <span role="columnheader">Method</span>
            <span role="columnheader">Parameters</span>
          </div>
          {methods.map(method => (
            <div className="sqd-atm-row" role="row" key={method.key}>
              <div className="sqd-atm-use" role="cell">
                <SqdCheckbox checked={method.use} onChange={use => patchMethod(method.key, { use })}>{method.label}</SqdCheckbox>
              </div>
              <div className="sqd-atm-params" role="cell">
                {method.params.map(param => (
                  <span className="sqd-inline-controls" key={param.key}>
                    <label className="sqd-label">{param.label}</label>
                    <SqdSpinner
                      ariaLabel={`${method.label} ${param.label}`}
                      value={param.value}
                      min={0}
                      max={10000}
                      disabled={!method.use}
                      onChange={v => patchParam(method.key, param.key, v)}
                    />
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
        <button type="button" className="sqd-btn" onClick={() => setAdding(true)}>Add new exit method</button>
      </SqdFieldset>
      {adding && <SqdModal title="Add new exit method" onClose={()=>setAdding(false)} footer={<button type="button" className="sqd-btn sqd-btn-primary" onClick={()=>{const method=atmDefaults.find(m=>m.key===selected)!;setMethods(items=>[...items,{...structuredClone(method),key:`local-${Date.now()}`,use:true}]);setAdding(false);}}>Add</button>}>
        <p className="sqd-gen-help">Local UI demo: choose an exit method from the fixture catalog.</p>
        <select aria-label="Exit method" value={selected} onChange={e=>setSelected(e.target.value)}>{atmDefaults.map(m=><option key={m.key} value={m.key}>{m.label}</option>)}</select>
      </SqdModal>}
    </div>
  );
}
