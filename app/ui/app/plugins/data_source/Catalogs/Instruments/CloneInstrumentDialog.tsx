import { useState } from 'react';
import { Button, Field, Modal, TextInput } from '../../../../components/ui';
import { useFileSymbols } from '../../FileImport/fileSymbolsStore';
import type { FileInstrument, InstrumentBroker } from '../../FileImport/fileSymbols';
import './instruments.css';

export function CloneInstrumentDialog({ source, brokers, onClose, onSaved }: { source:FileInstrument; brokers:InstrumentBroker[]; onClose:()=>void; onSaved:(message:string)=>void }) {
  const store=useFileSymbols(); const sourceBroker=brokers.find(row=>row.id===source.broker); const core=sourceBroker?.postfix && source.symbol.endsWith(sourceBroker.postfix) ? source.symbol.slice(0,-sourceBroker.postfix.length) : source.symbol;
  const [broker,setBroker]=useState('-1'); const [name,setName]=useState(`${core}Clone`); const [error,setError]=useState(''); const profile=brokers.find(row=>row.id===broker) ?? brokers[0];
  function save(){ try { store.addInstrument({ ...structuredClone(source), symbol:name+(profile.postfix??''), broker:profile.id, brokerName:profile.name, timezone:profile.timezone },brokers.map(row=>row.id)); onSaved('Instrument cloned.'); onClose(); } catch(cause){ setError(cause instanceof Error?cause.message:'Unable to clone instrument.'); } }
  return <div className="instruments-flow"><Modal title={`Clone instrument '${source.symbol}'`} width={520} onClose={onClose} footer={<><Button onClick={onClose}>Close</Button><Button className="primary" onClick={save}>Save</Button></>}>
    {(error||store.storageError)&&<p role="alert" className="instrument-error">{error||store.storageError}</p>}
    <Field label="New instrument broker profile"><select value={broker} onChange={event=>{setBroker(event.target.value);setError('');}}>{brokers.map(row=><option value={row.id} key={row.id}>{row.name}</option>)}</select></Field>
    <Field label="New instrument name"><div className="instrument-name-postfix"><TextInput value={name} onChange={event=>{setName(event.target.value);setError('');}}/><span>{profile.postfix}</span></div></Field>
  </Modal></div>;
}
