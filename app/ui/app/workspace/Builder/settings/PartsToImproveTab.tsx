import { useState } from 'react';
import { SqdCheckbox, SqdFieldset, SqdSelect } from './SettingsControls';
import { partsToImproveActions, partsToImproveDefaults, type PartsToImproveState } from './settingsFixtures';

/** "Parts to improve" tab (donor evidence SQX144-EV-000040). */
export function PartsToImproveTab() {
  const [state, setState] = useState<PartsToImproveState>(partsToImproveDefaults);
  const patch = (part: Partial<PartsToImproveState>) => setState(current => ({ ...current, ...part }));
  const actionOptions = partsToImproveActions.map(a => ({ value: a, label: a }));

  const rule = (
    label: 'LONG' | 'SHORT',
    use: boolean,
    onUse: (v: boolean) => void,
    action?: string,
    onAction?: (v: string) => void,
    note?: string,
    actionHidden?: boolean,
  ) => (
    <div className={`sqd-pti-rule${label === 'SHORT' ? ' short' : ''}`}>
      <SqdCheckbox checked={use} onChange={onUse}>{label}</SqdCheckbox>
      {action !== undefined && onAction !== undefined && (
        <SqdSelect ariaLabel={`${label} action`} value={action} onChange={onAction} options={actionOptions} width={220} disabled={actionHidden} />
      )}
      <label className="sqd-pti-note">{note}</label>
    </div>
  );

  return (
    <div id="partsToImproveContent" className="sqd-tab-content">
      <SqdFieldset legend="Choose parts to improve">
        <legend className="sqd-pti-sublegend">Entry rules</legend>
        {rule('LONG', state.entryLongUse, v => patch({ entryLongUse: v }), state.entryLongAction, v => patch({ entryLongAction: v }), 'Replace whole part or add new blocks (8 conditions)')}
        {rule('SHORT', state.entryShortUse, v => patch({ entryShortUse: v }), state.entryShortAction, v => patch({ entryShortAction: v }), 'Symmetric to Long', state.entryShortUse ? false : true)}

        <legend className="sqd-pti-sublegend" style={{ marginTop: 10 }}>Order types</legend>
        {rule('LONG', state.orderLongUse, v => patch({ orderLongUse: v }), undefined, undefined, state.orderLongUse ? 'Generate randomly' : 'Keep existing')}
        {rule('SHORT', state.orderShortUse, v => patch({ orderShortUse: v }), undefined, undefined, state.orderShortUse ? 'Generate randomly' : 'Keep existing')}

        <legend className="sqd-pti-sublegend" style={{ marginTop: 10 }}>Exit rules</legend>
        {rule('LONG', state.exitLongUse, v => patch({ exitLongUse: v }), state.exitLongAction, v => patch({ exitLongAction: v }), 'Keep existing (3 blocks)')}
        {rule('SHORT', state.exitShortUse, v => patch({ exitShortUse: v }), state.exitShortAction, v => patch({ exitShortAction: v }), 'Symmetric to Long', state.exitShortUse ? false : true)}

        <label className="sqd-pti-help">Note - If you want to change symmetry of entry or exit block, you can do it in What to build tab.</label>

        <legend className="sqd-pti-sublegend" style={{ marginTop: 10 }}>ATM - advanced exits</legend>
        <div className="sqd-pti-rule">
          <SqdCheckbox checked={state.improveAtm} onChange={improveAtm => patch({ improveAtm })}>Improve / generate (Ultimate version only)</SqdCheckbox>
          <button type="button" className="sqd-link-button" onClick={() => window.open("https://strategyquant.com/doc/strategyquant/parts-to-improve/", "_blank", "noopener")}>How it works</button>
        </div>
      </SqdFieldset>
    </div>
  );
}
