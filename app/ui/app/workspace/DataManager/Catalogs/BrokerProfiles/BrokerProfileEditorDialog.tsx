import { useState } from 'react';
import { Button, Field, Modal, TextInput } from '../../../../components/ui';
import { timezones } from '../../documents';
import { useDataManagerStore } from '../../Common/dataManagerStore';
import type { BrokerProfile } from './brokerProfiles';
import './brokerProfiles.css';
export function BrokerProfileEditorDialog({ mode, source, canSetStockPicker, canSetMt, canSetTimezone, onClose, onSaved }: {
    mode: 'add' | 'edit';
    source?: BrokerProfile;
    canSetStockPicker: boolean;
    canSetMt: boolean;
    canSetTimezone: boolean;
    onClose: () => void;
    onSaved: (message: string) => void;
}) {
    const store = useDataManagerStore();
    const [value, setValue] = useState<BrokerProfile>(() => source ? structuredClone(source) : { id: '', name: '', desc: '', postfix: '', timezone: timezones[0][0], mtUse: true, stockPickerUse: true, system: false, stocks: [], instruments: [] });
    const [error, setError] = useState('');
    async function save() {
        try {
            await store.saveBroker(value);
            onSaved(mode === 'add' ? 'Broker was added' : 'Broker was updated');
            onClose();
        }
        catch (cause) {
            setError(cause instanceof Error ? cause.message : 'Cannot save broker.');
        }
    }
    return <div className="broker-flow"><Modal title={`${mode === 'add' ? 'Add' : 'Edit'} Broker profile`} width={700} onClose={onClose} footer={<><Button onClick={onClose}>Close</Button><Button className="primary" onClick={save}>Save</Button></>}>
    {error && <p className="broker-error" role="alert">{error}</p>}<fieldset><Field label="Broker profile name *"><TextInput aria-label="Broker profile name" maxLength={50} value={value.name} onChange={event => setValue({ ...value, name: event.target.value })}/></Field><Field label="Description"><textarea aria-label="Broker description" maxLength={250} value={value.desc} onChange={event => setValue({ ...value, desc: event.target.value })}/></Field></fieldset>
    <fieldset><legend>Stockpicker functionality</legend><label className="broker-check"><input type="checkbox" checked={value.stockPickerUse} disabled={!canSetStockPicker} onChange={event => setValue({ ...value, stockPickerUse: event.target.checked })}/><span>Use this broker profile for filtering stocks<small>You will be able to edit available list using grid action</small></span></label></fieldset>
    <fieldset><legend>Metatrader 4/5 functionality</legend><label className="broker-check"><input type="checkbox" checked={value.mtUse} disabled={!canSetMt} onChange={event => setValue({ ...value, mtUse: event.target.checked })}/><span>Use this broker profile for instruments setting for MT4/5</span></label><Field label="Broker timezone"><select aria-label="Broker timezone" value={value.timezone} disabled={!canSetTimezone} onChange={event => setValue({ ...value, timezone: event.target.value })}>{timezones.map(([id, label]) => <option key={`${id}-${label}`} value={id}>{label}</option>)}</select></Field><Field label="Instrument/data postfix *"><TextInput aria-label="Instrument data postfix" maxLength={100} value={value.postfix} onChange={event => setValue({ ...value, postfix: event.target.value })}/></Field></fieldset>
  </Modal></div>;
}
