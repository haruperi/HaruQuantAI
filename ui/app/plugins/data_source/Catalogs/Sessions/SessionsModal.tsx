import { useRef, useState } from 'react';
import { Button, Checkbox, Field, Modal, TextInput } from '../../../../components/ui';
import { generateMondayFriday, validateIntervals, type CatalogSession, type SessionBroker, type SessionDefinition, type SessionElement } from './sessions';
import { useSessions } from './sessionStore';
import { SessionElementDialog } from './SessionElementDialog';
import './sessions.css';

export function SessionsModal({ mode, source, brokers, onClose, onSaved }: {
  mode: 'add' | 'edit' | 'clone'; source?: CatalogSession; brokers: SessionBroker[];
  onClose: () => void; onSaved: (message: string) => void;
}) {
  const [draft, setDraft] = useState<SessionDefinition>(() => source ? structuredClone(source) : { name: '', broker: '-1', brokerName: 'Default', description: '', timezone: 'UTC', holidays: [], isDefault: false, elements: [] });
  const [baseline, setBaseline] = useState(draft);
  const [name, setName] = useState(source ? source.name + 'Clone' : '');
  const [shift, setShift] = useState(0);
  const [selected, setSelected] = useState<number | null>(null);
  const [element, setElement] = useState<{ mode: 'add' | 'edit'; index?: number } | null>(null);
  const [discard, setDiscard] = useState(false);
  const [pending, setPending] = useState(false);
  const busy = useRef(false);
  const [error, setError] = useState('');
  const changed = mode === 'clone' ? name !== source?.name + 'Clone' || shift !== 0 : JSON.stringify(draft) !== JSON.stringify(baseline);
  function requestClose() { if (busy.current) return; if (element) setElement(null); else if (discard) setDiscard(false); else if (changed) setDiscard(true); else onClose(); }
  function applied(saved: CatalogSession) {
    setBaseline(saved); setDraft(current => ({ ...current, elements: saved.elements }));
    setSelected(null); setElement(null); onSaved('Session intervals saved.');
  }
  async function interval(value: SessionElement) {
    if (busy.current) return;
    const windows = [...draft.elements];
    if (element?.mode === 'edit' && element.index !== undefined) windows[element.index] = value; else windows.push(value);
    validateIntervals(windows);
    if (!source) { setDraft(current => ({ ...current, elements: windows })); setElement(null); setSelected(null); return; }
    busy.current = true; setPending(true);
    try { applied(await useSessions.getState().element(source.id, element?.mode === 'edit' ? 'update' : 'add', element?.index, value)); }
    finally { busy.current = false; setPending(false); }
  }
  async function schedule(action: 'generate' | 'remove') {
    if (busy.current) return;
    setError(''); busy.current = true; setPending(true);
    try {
      if (action === 'remove' && selected === null) throw new Error('Select a session interval.');
      const windows = action === 'generate' ? generateMondayFriday(draft.elements) : draft.elements.filter((_, index) => index !== selected);
      validateIntervals(windows);
      if (!source) { setDraft(current => ({ ...current, elements: windows })); setSelected(null); }
      else applied(action === 'remove' ? await useSessions.getState().element(source.id, 'remove', selected!) : await useSessions.getState().save({ ...baseline, elements: windows }));
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to save intervals.'); }
    finally { busy.current = false; setPending(false); }
  }
  async function save() {
    if (busy.current) return;
    busy.current = true; setPending(true); setError('');
    try {
      if (mode === 'clone') await useSessions.getState().clone(source!, name, shift);
      else {
        const broker = brokers.find(row => row.id === draft.broker);
        await useSessions.getState().save({ ...draft, name: mode === 'add' ? draft.name + (broker?.postfix ?? '') : draft.name });
      }
      onSaved(mode === 'clone' ? 'Session cloned.' : 'Session profile saved.'); onClose();
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to save session.'); }
    finally { busy.current = false; setPending(false); }
  }
  const choices = brokers.some(row => row.id === draft.broker) ? brokers : [...brokers, { id: draft.broker, name: draft.brokerName, postfix: '' }];
  return <div className="sessions-flow"><Modal title={mode === 'clone' ? 'Clone session' : mode === 'add' ? 'Add session template' : 'Edit session template'} width={800} onClose={requestClose} footer={<><Button disabled={pending} onClick={requestClose}>Close</Button><Button disabled={pending} className="primary" onClick={() => void save()}>{pending ? 'Saving…' : 'Save'}</Button></>}>
    {error && <p role="alert" className="session-error">{error}</p>}
    {pending && <p role="status">Saving session specifications…</p>}
    {!!source?.normalizationWarnings?.length && <div role="note" aria-label="Stored session compatibility"><p>This profile was loaded using legacy defaults:</p><ul>{source.normalizationWarnings.map(warning => <li key={warning}>{warning}</li>)}</ul><p>Saving a profile, changing intervals, or cloning explicitly writes canonical fields and defaults. Reading leaves the stored profile unchanged.</p></div>}
    <fieldset className="session-form-body" disabled={pending}>
    {mode === 'clone' ? <><p>Copy {source?.name}, preserving its broker, timezone and holiday dates.</p><Field label="New session name"><TextInput value={name} onChange={event => setName(event.target.value)}/></Field><Field label="Shift schedule (minutes)"><TextInput type="number" step={1} min={-1440} max={1440} value={Number.isNaN(shift) ? '' : shift} onChange={event => setShift(event.target.valueAsNumber)}/></Field><p>This adjusts recurring local times and weekdays. It does not convert timezones or shift holidays.</p></> : <>
      <div className="session-template-fields">
        <Field label="Session name"><TextInput disabled={mode === 'edit'} value={draft.name} onChange={event => setDraft({ ...draft, name: event.target.value })}/></Field>
        <Field label="Broker profile"><select value={draft.broker} onChange={event => setDraft({ ...draft, broker: event.target.value })}>{choices.map(row => <option key={row.id} value={row.id}>{row.name}</option>)}</select></Field>
        <Field label="Timezone"><TextInput value={draft.timezone ?? 'UTC'} placeholder="America/New_York" onChange={event => setDraft({ ...draft, timezone: event.target.value })}/></Field>
        <Field label="Description"><TextInput value={draft.description ?? ''} onChange={event => setDraft({ ...draft, description: event.target.value })}/></Field>
      </div>
      <Checkbox label="Default profile" checked={draft.isDefault ?? false} onChange={isDefault => setDraft({ ...draft, isDefault })}/>
      <fieldset><legend>Session intervals</legend>
        <p>{source ? 'Interval changes save immediately. Profile fields and holidays save with Save.' : 'Intervals stay in this draft until Save.'} Times are local to the configured timezone. Lunch pauses are gaps between open intervals.</p>
        <div className="session-elements-grid"><table className="plain-table" aria-label="Session elements"><thead><tr>{['#','Start day','Start time','End day','End time','EOD','Type'].map(label => <th key={label}>{label}</th>)}</tr></thead><tbody>
          {draft.elements.map((row,index) => <tr key={index} className={selected === index ? 'selected' : ''} onClick={() => setSelected(index)} onDoubleClick={() => { setSelected(index); setElement({ mode: 'edit', index }); }}><td>{index + 1}</td><td>{row.dayFrom}</td><td>{row.timeFrom}</td><td>{row.dayTo}</td><td>{row.timeTo}</td><td>{row.eod ? 'Yes' : 'No'}</td><td>{row.sessionType ?? 'Regular'}</td></tr>)}
          {!draft.elements.length && <tr><td colSpan={7}>No intervals configured; this profile is closed.</td></tr>}
        </tbody></table></div>
        <div className="session-element-actions"><Button onClick={() => setElement({ mode: 'add' })}>Add interval</Button><Button onClick={() => void schedule('generate')}>Add Mon-Fri</Button><Button onClick={() => { if (selected === null) setError('Select a session interval.'); else setElement({ mode: 'edit', index: selected }); }}>Edit interval</Button><Button onClick={() => void schedule('remove')}>Remove interval</Button></div>
      </fieldset>
      <fieldset><legend>Full-day holidays</legend><p>Dates close the profile in its configured timezone.</p>
        {(draft.holidays ?? []).map((holiday,index) => <div className="session-holiday-fields" key={index}><Field label={`Holiday date ${index + 1}`}><TextInput type="date" value={holiday.date_str} onChange={event => setDraft({ ...draft, holidays: draft.holidays!.map((row,i) => i === index ? { ...row, date_str: event.target.value } : row) })}/></Field><Field label={`Holiday description ${index + 1}`}><TextInput value={holiday.description} onChange={event => setDraft({ ...draft, holidays: draft.holidays!.map((row,i) => i === index ? { ...row, description: event.target.value } : row) })}/></Field><Button aria-label={`Remove holiday ${index + 1}`} onClick={() => setDraft({ ...draft, holidays: draft.holidays!.filter((_,i) => i !== index) })}>Remove</Button></div>)}
        <Button onClick={() => setDraft({ ...draft, holidays: [...draft.holidays ?? [], { date_str: '', description: '' }] })}>Add holiday</Button>
      </fieldset>
    </>}
    </fieldset>
  </Modal>
    {element && <SessionElementDialog mode={element.mode} value={element.index !== undefined ? draft.elements[element.index] : undefined} onClose={() => { if (!busy.current) setElement(null); }} onSave={interval}/>}
    {discard && <Modal title="Changes not saved" width={470} onClose={() => setDiscard(false)} footer={<><Button onClick={() => setDiscard(false)}>No</Button><Button onClick={onClose}>Yes</Button></>}><p>Discard unsaved profile changes? Confirmed interval changes remain saved.</p></Modal>}
  </div>;
}
