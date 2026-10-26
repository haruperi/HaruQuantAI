import { useRef, useState } from 'react';
import { Button, Field, Modal, TextInput } from '../../../../components/ui';
import { timezones } from '../../FileImport/fileImport';
import { useDataManagerStore } from '../../Common/dataManagerStore';
import type { BrokerProfile } from './brokerProfiles';
import './brokerProfiles.css';

export function BrokerProfilesModal({mode,source,canSetStockPicker,canSetMt,canSetTimezone,onClose,onSaved}:{mode:'add'|'edit';source?:BrokerProfile;canSetStockPicker:boolean;canSetMt:boolean;canSetTimezone:boolean;onClose:()=>void;onSaved:(message:string)=>void}) {
  const [value,setValue] = useState<BrokerProfile>(() => source ? structuredClone(source) : {id:'',name:'',desc:'',postfix:'',timezone:'UTC',mtUse:true,stockPickerUse:true,system:false,stocks:[],symbols:[],spreadModel:{model:'inherit'},commissionModel:{model:'inherit'}});
  const [error,setError] = useState('');
  const [clockPolicy,setClockPolicy] = useState(()=>JSON.stringify(source?.clockPolicy??{},null,2));
  const [pending,setPending] = useState(false);
  const submitting = useRef(false);
  function close() { if (!submitting.current) onClose(); }
  async function save() {
    if (submitting.current) return;
    submitting.current = true; setPending(true); setError('');
    try {
      const policy:unknown=JSON.parse(clockPolicy);
      if(!policy||typeof policy!=='object'||Array.isArray(policy))throw new Error('Clock policy must be a JSON object.');
      await useDataManagerStore.getState().saveBroker({...value,clockPolicy:policy as Record<string,unknown>});
      onSaved(mode === 'add' ? 'Broker was added' : 'Broker was updated'); onClose();
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Cannot save broker.'); }
    finally { submitting.current = false; setPending(false); }
  }
  return <div className="broker-flow"><Modal title={`${mode === 'add' ? 'Add' : 'Edit'} Broker profile`} width={700} onClose={close} footer={<><Button disabled={pending} onClick={close}>Close</Button><Button disabled={pending} className="primary" onClick={() => void save()}>{pending ? 'Saving…' : 'Save'}</Button></>}>
    {error && <p className="broker-error" role="alert">{error}</p>}
    <fieldset disabled={pending}><Field label="Broker profile name *"><TextInput aria-label="Broker profile name" maxLength={50} value={value.name} onChange={e => setValue({...value,name:e.target.value})}/></Field><Field label="Description"><textarea aria-label="Broker description" maxLength={250} value={value.desc} onChange={e => setValue({...value,desc:e.target.value})}/></Field></fieldset>
    <fieldset disabled={pending}><legend>Stockpicker functionality</legend><label className="broker-check"><input aria-label="Enable stock filtering" type="checkbox" checked={value.stockPickerUse} disabled={!canSetStockPicker} onChange={e => setValue({...value,stockPickerUse:e.target.checked})}/>Use this broker profile for filtering stocks</label></fieldset>
    <fieldset disabled={pending}><legend>Symbol and session settings</legend><label className="broker-check"><input aria-label="Enable symbol settings" type="checkbox" checked={value.mtUse} disabled={!canSetMt} onChange={e => setValue({...value,mtUse:e.target.checked})}/>Use this profile for symbols and sessions</label><Field label="Broker timezone"><select aria-label="Broker timezone" disabled={!canSetTimezone} value={value.timezone} onChange={e => setValue({...value,timezone:e.target.value})}>{!timezones.some(([id])=>id===value.timezone)&&<option value={value.timezone}>{value.timezone}</option>}{timezones.map(([id,label]) => <option key={`${id}-${label}`} value={id}>{label}</option>)}</select></Field><Field label="Symbol/data postfix"><TextInput aria-label="Symbol data postfix" maxLength={100} value={value.postfix} onChange={e => setValue({...value,postfix:e.target.value})}/></Field></fieldset>
    <fieldset disabled={pending}><legend>Clock policy</legend><Field label="Clock policy JSON"><textarea aria-label="Clock policy JSON" value={clockPolicy} onChange={e=>setClockPolicy(e.target.value)}/></Field><Field label="Clock policy revision"><input aria-label="Clock policy revision" type="number" min={0} step={1} value={value.clockPolicyRevision??0} onChange={e=>setValue({...value,clockPolicyRevision:e.target.valueAsNumber})}/></Field></fieldset>
    {mode==='edit'&&<fieldset><legend>Database record</legend><Field label="ID"><TextInput aria-label="Broker ID" readOnly value={value.id}/></Field><Field label="Created at UTC"><TextInput aria-label="Broker created at UTC" readOnly value={value.createdAt??''}/></Field><Field label="Updated at UTC"><TextInput aria-label="Broker updated at UTC" readOnly value={value.updatedAt??''}/></Field></fieldset>}
    <fieldset disabled={pending}><legend>Profile status</legend><label className="broker-check"><input aria-label="System broker profile" type="checkbox" checked={value.system} onChange={e=>setValue({...value,system:e.target.checked})}/>System profile</label><label className="broker-check"><input aria-label="Broker enabled" type="checkbox" checked={value.enabled ?? true} onChange={e=>setValue({...value,enabled:e.target.checked})}/>Enabled</label></fieldset>
  </Modal></div>;
}
