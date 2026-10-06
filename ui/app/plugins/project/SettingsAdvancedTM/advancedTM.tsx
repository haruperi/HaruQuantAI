import { useAdvancedTMController } from './AdvancedTMCtrl';
import { AddNewExitPopup } from './addNewExitPopup';
import { SqdCheckbox, SqdFieldset, SqdSpinner } from '../ProjectWorkbench/settings/SettingsControls';

/**
 * "ATM" tab (donor evidence retained target UI; current donor equivalence unverified): Advanced Trade Management
 * surface. The donor editor is 1,206 template lines of method/parameter
 * tables; this is the donor-style structure with the demo method set
 * derived from the exit formulas of the Build template.
 */
export function AtmTab() {
  const { adding, setAdding, selected, setSelected, methods, patchMethod, patchParam, addExit } = useAdvancedTMController();

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
      {adding && <AddNewExitPopup selected={selected} setSelected={setSelected} setAdding={setAdding} addExit={addExit} />}
    </div>
  );
}
