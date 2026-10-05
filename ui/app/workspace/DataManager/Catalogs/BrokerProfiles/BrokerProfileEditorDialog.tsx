import { useEffect, useState } from 'react';
import { Button, Field, Modal, TextInput } from '../../../../components/ui';
import { timezones } from '../../documents';
import { useDataManagerStore } from '../../Common/dataManagerStore';
import type { BrokerProfile } from './brokerProfiles';
import './brokerProfiles.css';
import { brokerClockPort, type ClockPolicyResponse } from '../../Common/catalogClient';

function BrokerClockEditor({ brokerId }: { brokerId: string }) {
    const [response, setResponse] = useState<ClockPolicyResponse>();
    const [draft, setDraft] = useState<Record<string, unknown>>({});
    const [error, setError] = useState('');
    const [busy, setBusy] = useState(false);
    const [saved, setSaved] = useState('');
    const [invalidArrays, setInvalidArrays] = useState<Set<string>>(new Set());
    useEffect(() => {
        let active = true;
        brokerClockPort.read(brokerId).then(value => {
            if (!active) return;
            setResponse(value);
            setDraft(Object.fromEntries(Object.entries(value.schema.properties).filter(([, schema]) => schema.default !== undefined).map(([key, schema]) => [key, schema.default])));
        }).catch(cause => { if (active) setError(cause instanceof Error ? cause.message : 'Clock policy unavailable.'); });
        return () => { active = false; };
    }, [brokerId]);
    async function save(): Promise<void> {
        if (!response || invalidArrays.size > 0) return;
        setBusy(true); setError(''); setSaved('');
        try {
            const value = await brokerClockPort.write(brokerId, response.revision, { ...draft, revision: response.revision + 1, schema_version: 1 });
            setResponse(value); setSaved(`Saved policy revision ${value.revision}. Existing imports remain unchanged.`);
        } catch (cause) { setError(cause instanceof Error ? cause.message : 'Clock policy could not be saved.'); }
        finally { setBusy(false); }
    }
    return <fieldset><legend>Historical broker clock policy</legend>
      {error && <p role="alert">{error}</p>}
      {saved && <p role="status">{saved}</p>}
      {response && <>
        <p>Database broker: {response.database_broker_id}. Stored revisions: {response.revisions.length}. Add a new effective interval; previous policies remain preserved.</p>
        <details><summary>Existing policies</summary><pre>{JSON.stringify(response.revisions, null, 2)}</pre></details>
        {Object.entries(response.schema.properties).filter(([key]) => !['revision', 'schema_version'].includes(key)).map(([key, schema]) => <Field key={key} label={schema.title ?? key}>
          {schema.enum ? <select aria-label={schema.title ?? key} value={String(draft[key] ?? '')} onChange={event => setDraft({ ...draft, [key]: event.target.value })}><option value="">Choose…</option>{schema.enum.map(value => <option key={String(value)}>{String(value)}</option>)}</select>
          : schema.type === 'boolean' ? <input type="checkbox" aria-label={schema.title ?? key} checked={draft[key] === true} onChange={event => setDraft({ ...draft, [key]: event.target.checked })}/>
          : schema.type === 'array' ? <textarea aria-label={schema.title ?? key} placeholder={key === 'transitions' ? 'UTC transition schedule as a JSON array' : 'Evidence references as a JSON array'} defaultValue="[]" onChange={event => { try { const value: unknown = JSON.parse(event.target.value); if (!Array.isArray(value)) throw new Error('Array required'); setDraft({ ...draft, [key]: value }); setInvalidArrays(previous => { const next = new Set(previous); next.delete(key); return next; }); } catch { setInvalidArrays(previous => new Set(previous).add(key)); } }}/>
          : <input aria-label={schema.title ?? key} type={schema.type === 'integer' ? 'number' : 'text'} min={schema.minimum} max={schema.maximum} placeholder={schema.format === 'date-time' ? '2026-01-01T00:00:00Z' : undefined} value={String(draft[key] ?? '')} onChange={event => setDraft({ ...draft, [key]: schema.type === 'integer' ? Number(event.target.value) : event.target.value })}/>}
        </Field>)}
        <p>Verified means the stated tick, bar, request and historical transition semantics have supporting evidence. A current tick estimate alone does not verify history.</p>
        {invalidArrays.size > 0 && <p role="alert">Enter valid JSON arrays before saving.</p>}
        <Button disabled={busy || invalidArrays.size > 0} onClick={() => void save()}>{busy ? 'Saving policy…' : 'Save new clock policy'}</Button>
      </>}
    </fieldset>;
}
export function BrokerClockPolicyDialog({ source, onClose }: {
    source: BrokerProfile;
    onClose: () => void;
}) {
    return <div className="broker-flow"><Modal title={`${source.name} clock policy`} width={700} onClose={onClose} footer={<Button onClick={onClose}>Close</Button>}>
      <BrokerClockEditor brokerId={source.id}/>
    </Modal></div>;
}
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
    <Field label="Database broker association"><TextInput aria-label="Database broker association" placeholder="Existing database broker ID" value={value.databaseBrokerId ?? ''} disabled={Boolean(source?.databaseBrokerId)} onChange={event => setValue({ ...value, databaseBrokerId: event.target.value || undefined })}/></Field>
    {source?.id && <BrokerClockEditor brokerId={source.id}/>}
  </Modal></div>;
}
