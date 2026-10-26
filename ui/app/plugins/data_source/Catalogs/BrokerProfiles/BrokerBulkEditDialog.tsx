import { useRef, useState } from 'react';
import { Button, Field, Modal, TextInput } from '../../../../components/ui';
import { editBrokerCatalog } from './brokerApiClient';
import { useDataManagerStore } from '../../Common/dataManagerStore';

export function BrokerBulkEditDialog({ids,onClose,onSaved}:{ids:string[];onClose:()=>void;onSaved:(message:string)=>void}) {
  const [field,setField]=useState('description');
  const [value,setValue]=useState('');
  const [flag,setFlag]=useState(true);
  const [pending,setPending]=useState(false);
  const [error,setError]=useState('');
  const busy=useRef(false);
  const boolean=['enabled','mt_use','stockpicker_use','is_system'].includes(field);
  async function save() {
    if(busy.current)return;
    busy.current=true;setPending(true);setError('');
    try {
      const parsed=field==='clock_policy'?JSON.parse(value):field==='clock_policy_revision'?Number(value):boolean?flag:value;
      await editBrokerCatalog(ids,{[field]:parsed});
      await useDataManagerStore.getState().syncBrokers();
      onSaved(`${ids.length} brokers updated`);onClose();
    }catch(cause){setError(cause instanceof Error?cause.message:'Unable to update brokers.');}
    finally{busy.current=false;setPending(false);}
  }
  return <div className="broker-flow"><Modal title="Edit selected brokers" width={560} onClose={()=>{if(!busy.current)onClose();}} footer={<><Button disabled={pending} onClick={onClose}>Close</Button><Button disabled={pending} className="primary" onClick={()=>void save()}>{pending?'Saving…':'Save'}</Button></>}>
    {error&&<p role="alert" className="broker-error">{error}</p>}
    <p>Apply one field to {ids.length} selected brokers.</p><fieldset disabled={pending}>
    <Field label="Field"><select aria-label="Broker field" value={field} onChange={event=>setField(event.target.value)}>{[['description','Description'],['server_timezone','Timezone'],['postfix','Postfix'],['is_system','System profile'],['clock_policy','Clock policy JSON'],['clock_policy_revision','Clock policy revision'],['enabled','Enabled'],['mt_use','Symbols and sessions'],['stockpicker_use','Stock filtering']].map(([key,label])=><option value={key} key={key}>{label}</option>)}</select></Field>
    <Field label="Value">{boolean?<select aria-label="Broker field value" value={String(flag)} onChange={event=>setFlag(event.target.value==='true')}><option value="true">Yes</option><option value="false">No</option></select>:<TextInput aria-label="Broker field value" value={value} onChange={event=>setValue(event.target.value)}/>}</Field>
    </fieldset>
  </Modal></div>;
}
