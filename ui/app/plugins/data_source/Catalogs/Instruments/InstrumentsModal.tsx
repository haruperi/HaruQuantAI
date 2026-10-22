import { useRef, useState } from 'react';
import { Button, Field, Modal, TextInput } from '../../../../components/ui';
import { newInstrument, type FileInstrument, type InstrumentBroker, type InstrumentMassPatch } from '../../FileImport/fileSymbols';
import { commissionInfo, type CatalogInstrument } from './instrumentsApiClient';
import { useInstruments } from './instrumentsStore';
import { InstrumentDetailsFields } from './InstrumentDetailsFields';
import './instruments.css';

export function InstrumentsModal({ mode, selected, brokers, onClose, onSaved }: {
  mode: 'add' | 'edit' | 'mass' | 'clone'; selected: CatalogInstrument[];
  brokers: InstrumentBroker[]; onClose: () => void; onSaved: (message: string) => void;
}) {
  const [draft, setDraft] = useState<FileInstrument>(() => selected[0] ? structuredClone(selected[0]) : { ...newInstrument(), marginRate: 0.05, decimals: 5, minVolume: 0.01, maxVolume: 100, lotStep: 0.01, tickValue: 10 });
  const [flags, setFlags] = useState<InstrumentMassPatch['fields']>({});
  const [name, setName] = useState(selected[0] ? selected[0].symbol + 'Clone' : '');
  const [error, setError] = useState('');
  const [pending, setPending] = useState(false);
  const submitting = useRef(false);
  const title = { add: 'Add instrument', edit: 'Edit instrument', mass: 'Mass-Edit instrument', clone: 'Clone instrument' }[mode];
  const close = () => { if (!submitting.current) onClose(); };
  async function save() {
    if (submitting.current) return;
    submitting.current = true; setPending(true); setError('');
    try {
      const store = useInstruments.getState();
      if (mode === 'add') {
        if (!(Number(draft.contractSize) > 0) || !(Number(draft.pipSize) > 0)) throw new Error('Enter positive contract and pip sizes.');
        const profile = brokers.find(row => row.id === draft.broker);
        await store.addInstrument({ ...draft, symbol: draft.symbol + (profile?.postfix ?? '') });
      } else if (mode === 'clone') await store.cloneInstrument(selected[0], name);
      else if (mode === 'edit') await store.editInstrument(selected[0], draft);
      else await store.massEditInstruments(selected.map(row => row.id), { fields: flags, value: draft });
      onSaved(mode === 'clone' ? 'Instrument cloned.' : mode === 'add' ? 'Instrument added.' : 'Instruments modified.');
      onClose();
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to save instrument.'); }
    finally { submitting.current = false; setPending(false); }
  }
  const commission = selected[0] ? commissionInfo(selected[0].record.commissions) : null;
  const choices = [...brokers];
  if (!choices.some(row => row.id === draft.broker)) choices.push({ id: draft.broker, name: draft.brokerName, timezone: draft.timezone, postfix: '' });
  return <div className="instruments-flow"><Modal title={title} width={720} onClose={close} footer={<><Button disabled={pending} onClick={close}>Close</Button><Button disabled={pending} className="primary" onClick={() => void save()}>{pending ? 'Saving…' : 'Save'}</Button></>}>
    {error && <p className="instrument-error" role="alert">{error}</p>}
    {pending && <p role="status">Saving instrument specifications…</p>}
    <fieldset className="instrument-form-body" disabled={pending}>
      {mode === 'clone' ? <><p>Copy the complete saved specification for {selected[0].symbol}, retaining its broker profile.</p><Field label="New instrument name"><TextInput value={name} maxLength={128} onChange={event => setName(event.target.value)}/></Field></> : <>
        {selected[0]?.record.swap_settings === null && <p>Legacy swap type and rollover time are unspecified. Editing swap settings explicitly configures them.</p>}
        {commission && <p title={commission.details}>{commission.summary}. Other edits preserve commission settings.</p>}
        <InstrumentDetailsFields value={draft} onChange={setDraft} brokers={choices} identityLocked={mode === 'edit'} massFlags={mode === 'mass' ? flags : undefined} onMassFlags={setFlags}/>
      </>}
    </fieldset>
  </Modal></div>;
}
