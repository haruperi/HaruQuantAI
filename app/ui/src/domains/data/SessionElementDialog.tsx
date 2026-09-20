import { useState } from 'react';
import { Button, Checkbox, Field, Modal, Select, TextInput } from '../../components/ui';
import { sessionDays, validateElement, type SessionElement } from './sessions';

export function SessionElementDialog({ value, mode, onClose, onSave }:{value?:SessionElement;mode:'add'|'edit';onClose:()=>void;onSave:(value:SessionElement)=>void}){
  const [draft,setDraft]=useState<SessionElement>(value?structuredClone(value):{dayFrom:'Mon',timeFrom:'00:00',dayTo:'Mon',timeTo:'23:59',eod:false});const [error,setError]=useState('');
  function save(){try{validateElement(draft);onSave(draft);}catch(cause){setError(cause instanceof Error?cause.message:'Invalid session.');}}
  return <div className="sessions-flow"><Modal title={`${mode==='add'?'Add':'Edit'} session`} width={480} onClose={onClose} footer={<><Button onClick={onClose}>Close</Button><Button className="primary" onClick={save}>Save</Button></>}>
    {error&&<p className="session-error" role="alert">{error}</p>}
    <fieldset><legend>Session</legend><div className="session-element-fields">
      <Field label="Start day"><Select value={draft.dayFrom} onChange={dayFrom=>setDraft({...draft,dayFrom:dayFrom as SessionElement['dayFrom']})}>{sessionDays.map(day=><option key={day}>{day}</option>)}</Select></Field>
      <Field label="Start time"><TextInput aria-label="Start time" type="time" step={120} value={draft.timeFrom} onChange={event=>setDraft({...draft,timeFrom:event.target.value})}/></Field>
      <Field label="End day"><Select value={draft.dayTo} onChange={dayTo=>setDraft({...draft,dayTo:dayTo as SessionElement['dayTo']})}>{sessionDays.map(day=><option key={day}>{day}</option>)}</Select></Field>
      <Field label="End time"><TextInput aria-label="End time" type="time" step={120} value={draft.timeTo} onChange={event=>setDraft({...draft,timeTo:event.target.value})}/></Field>
    </div><Checkbox label="Session End Means EOD" checked={draft.eod} onChange={eod=>setDraft({...draft,eod})}/></fieldset>
  </Modal></div>;
}
