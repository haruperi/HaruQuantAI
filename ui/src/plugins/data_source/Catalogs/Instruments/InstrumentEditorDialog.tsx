import { useState } from 'react';
import { Button, Modal } from '../../../../components/ui';
import { applyMassPatch, newInstrument, validateInstrument, type FileInstrument, type InstrumentBroker, type InstrumentMassPatch } from '../../FileImport/fileSymbols';
import { useFileSymbols } from '../../FileImport/fileSymbolsStore';
import { InstrumentDetailsFields } from './InstrumentDetailsFields';
import './instruments.css';

export function InstrumentEditorDialog({ mode, selected, brokers, onClose, onSaved }: { mode:'add'|'edit'|'mass'; selected:FileInstrument[]; brokers:InstrumentBroker[]; onClose:()=>void; onSaved:(message:string)=>void }) {
  const store = useFileSymbols(); const base = selected[0] ? structuredClone(selected[0]) : newInstrument();
  const [draft,setDraft] = useState<FileInstrument>(base); const [flags,setFlags] = useState<InstrumentMassPatch['fields']>({}); const [error,setError] = useState('');
  const title = mode === 'add' ? 'Add instrument' : mode === 'edit' ? 'Edit instrument' : 'Mass-Edit instrument';
  function save(): void { try {
    const brokerIds = brokers.map(row => row.id);
    if (mode === 'add') { const profile = brokers.find(row => row.id === draft.broker); const value = { ...draft, symbol:draft.symbol + (profile?.postfix ?? ''), brokerName:profile?.name ?? 'Default', timezone:profile?.timezone ?? draft.timezone }; store.addInstrument(value,brokerIds); }
    else if (mode === 'edit') store.editInstrument(selected[0].symbol,draft,brokerIds);
    else { if (!Object.values(flags).some(Boolean)) throw new Error('You have to select some field for change.'); const updates = selected.map(item => applyMassPatch(item,{ fields:flags,value:draft })); for (const item of updates) validateInstrument(item,[],brokerIds); store.replaceInstruments(updates,brokerIds); }
    onSaved(mode === 'add' ? 'Instrument added' : mode === 'edit' ? 'Instrument modified' : 'Instruments modified'); onClose();
  } catch(cause){ setError(cause instanceof Error ? cause.message : 'Unable to save instrument.'); } }
  return <div className="instruments-flow"><Modal title={title} width={700} onClose={onClose} footer={<><Button onClick={onClose}>Close</Button><Button className="primary" onClick={save}>Save</Button></>}>
    {(error || store.storageError) && <p role="alert" className="instrument-error">{error || store.storageError}</p>}
    <InstrumentDetailsFields value={draft} onChange={value => { setDraft(value); setError(''); }} brokers={brokers} identityLocked={mode === 'edit'} massFlags={mode === 'mass' ? flags : undefined} onMassFlags={setFlags}/>
  </Modal></div>;
}
