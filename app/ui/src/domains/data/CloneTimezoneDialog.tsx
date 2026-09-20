import { useState } from 'react';
import { Button, Checkbox, Field, Modal, Select, TextInput } from '../../components/ui';
import { cloneTimeLabel, toolTimezones, type CloneSettings, type ToolTarget } from './dataTools';
import { useDataTools } from './dataToolsStore';
import './dataTools.css';

export function CloneTimezoneDialog({ targets, existingNames, externalActive, onClose, onStarted }: {
  targets: ToolTarget[]; existingNames: string[]; externalActive: boolean; onClose: () => void; onStarted: () => void;
}) {
  const store = useDataTools();
  const [settings, setSettings] = useState<CloneSettings>({ ...store.settings, postfix: '_{timeframe}_{cloneTime}' });
  const [error, setError] = useState('');
  const selectedFor = targets.length === 1 ? targets[0].symbol : 'multiple';
  const patch = (value: Partial<CloneSettings>) => { setSettings(current => ({ ...current, ...value })); setError(''); };
  function proceed(): void {
    try { store.startClone(targets, settings, existingNames, externalActive); onStarted(); onClose(); }
    catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to start clone.'); }
  }
  return <div className="data-tools-flow"><Modal title={`Clone to Timezone for '${selectedFor}'`} width={600} onClose={onClose}
    footer={<><Button onClick={onClose}>Close</Button><Button className="primary" onClick={proceed}>Proceed</Button></>}>
    {(error || store.storageError) && <p className="tools-error" role="alert">{error || store.storageError}</p>}
    <p className="tools-copy">Clone to Timezone creates a copy of the source data with all times recomputed in a different timezone.<br/>This way you can use one source data to create multiple “clones”, each in its own timezone.</p>
    <fieldset><legend>Data settings</legend>
      <Field label="Source data symbol name"><TextInput value={selectedFor} readOnly/></Field>
      <Field label="Cloned data symbol postfix" hint="Constants: {timeframe}, {cloneTime}"><TextInput aria-label="Cloned data symbol postfix" maxLength={80} value={settings.postfix} onChange={event => patch({ postfix: event.target.value })}/></Field>
    </fieldset>
    <fieldset><legend>Cloned data timezone</legend><div className="clone-timezone-options">
      <label><input type="radio" name="timezone-mode" checked={settings.timezoneType === 'shift'} onChange={() => patch({ timezoneType: 'shift' })}/><span>add fixed shift</span><TextInput aria-label="Fixed timezone shift" type="number" min={-23} max={23} step={1} disabled={settings.timezoneType !== 'shift'} value={settings.shiftHours} onChange={event => patch({ shiftHours: Number(event.target.value) })}/><small>hours</small></label>
      <label><input type="radio" name="timezone-mode" checked={settings.timezoneType === 'zone'} onChange={() => patch({ timezoneType: 'zone' })}/><span>choose timezone</span><Select disabled={settings.timezoneType !== 'zone'} value={settings.timezone} onChange={timezone => patch({ timezone })}>{toolTimezones.map(item => <option key={item}>{item}</option>)}</Select></label>
      <Checkbox label="Remove weekends" checked={settings.removeWeekends} onChange={removeWeekends => patch({ removeWeekends })}/>
    </div></fieldset>
    <p className="tools-mock-note">Offline mock clone. Generated rows will use <strong>{cloneTimeLabel(settings)}</strong>; source files are not modified.</p>
  </Modal></div>;
}
