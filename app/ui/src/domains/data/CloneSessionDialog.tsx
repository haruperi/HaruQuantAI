import { useState } from 'react';
import { Button, Field, Modal, Select, TextInput } from '../../components/ui';
import { finalSessionName, sessionCoreName, type SessionBroker, type SessionDefinition } from './sessions';
import { useSessions } from './sessionStore';
import './sessions.css';
export function CloneSessionDialog({source,brokers,onClose,onSaved}:{source:SessionDefinition;brokers:SessionBroker[];onClose:()=>void;onSaved:(message:string)=>void}){
  const store=useSessions();const sourceBroker=brokers.find(row=>row.id===source.broker);const [brokerId,setBrokerId]=useState('-1');const [name,setName]=useState(sessionCoreName(source.name,sourceBroker)+'Clone');const [error,setError]=useState('');const broker=brokers.find(row=>row.id===brokerId)??brokers[0];
  function save(){try{store.clone({...structuredClone(source),name:finalSessionName(name,broker),broker:broker.id,brokerName:broker.name},brokers.map(row=>row.id));onSaved('Session cloned');onClose();}catch(cause){setError(cause instanceof Error?cause.message:'Unable to clone session.');}}
  return <div className="sessions-flow"><Modal title={`Clone session '${source.name}'`} width={520} onClose={onClose} footer={<><Button onClick={onClose}>Close</Button><Button className="primary" onClick={save}>Save</Button></>}>
    {(error||store.storageError)&&<p className="session-error" role="alert">{error||store.storageError}</p>}<Field label="New session broker profile"><Select value={brokerId} onChange={setBrokerId}>{brokers.map(row=><option value={row.id} key={row.id}>{row.name}</option>)}</Select></Field><Field label="New session name"><div className="session-name-postfix"><TextInput aria-label="New session name" value={name} onChange={event=>setName(event.target.value)}/><span>{broker.postfix}</span></div></Field>
  </Modal></div>;
}
