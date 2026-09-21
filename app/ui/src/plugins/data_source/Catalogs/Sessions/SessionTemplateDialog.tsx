import { useMemo, useState } from 'react';
import { Button, Field, Modal, Select, TextInput } from '../../../../components/ui';
import { finalSessionName, generateMondayFriday, type SessionBroker, type SessionDefinition, type SessionElement } from './sessions';
import { useSessions } from './sessionStore';
import { SessionElementDialog } from './SessionElementDialog';
import './sessions.css';

export function SessionTemplateDialog({mode,source,brokers,onClose,onSaved}:{mode:'add'|'edit';source?:SessionDefinition;brokers:SessionBroker[];onClose:()=>void;onSaved:(message:string)=>void}){
  const store=useSessions();const initial=useMemo(()=>source?structuredClone(source):{name:'',broker:'-1',brokerName:'Default',elements:[]} satisfies SessionDefinition,[source]);
  const [draft,setDraft]=useState(initial);const [core,setCore]=useState('');const [selected,setSelected]=useState<number|null>(null);const [element,setElement]=useState<{mode:'add'|'edit';index?:number}|null>(null);const [error,setError]=useState('');const [discard,setDiscard]=useState(false);
  const broker=brokers.find(row=>row.id===draft.broker)??brokers[0];const changed=JSON.stringify(draft)!==JSON.stringify(initial)||(mode==='add'&&core!=='' );
  function requestClose(){if(changed)setDiscard(true);else onClose();}
  function modalClose(){if(element)setElement(null);else if(discard)setDiscard(false);else requestClose();}
  function save(){try{if(mode==='add'){const item={...draft,name:finalSessionName(core,broker),brokerName:broker.name};store.add(item,brokers.map(row=>row.id));}else store.edit(source!.name,draft,brokers.map(row=>row.id));onSaved(mode==='add'?'Session added':'Session modified');onClose();}catch(cause){setError(cause instanceof Error?cause.message:'Unable to save session.');}}
  function requireSelection():number|null{if(selected===null){setError('You must select at least one row');return null;}return selected;}
  function saveElement(value:SessionElement){if(element?.mode==='edit'&&element.index!==undefined){const elements=[...draft.elements];elements[element.index]=value;setDraft({...draft,elements});}else setDraft({...draft,elements:[...draft.elements,value]});setSelected(null);setElement(null);setError('');}
  return <div className="sessions-flow"><Modal title={`${mode==='add'?'Add':'Edit'} session template`} width={620} onClose={modalClose} footer={<><Button onClick={requestClose}>Close</Button><Button className="primary" onClick={save}>Save</Button></>}>
    {(error||store.storageError)&&<p className="session-error" role="alert">{error||store.storageError}</p>}
    <div className="session-template-fields"><Field label="Session name"><div className="session-name-postfix"><TextInput aria-label="Session name" disabled={mode==='edit'} value={mode==='edit'?draft.name:core} onChange={event=>{setCore(event.target.value);setError('');}}/><span>{mode==='add'?broker.postfix:''}</span></div></Field>
      <Field label="Broker profile *"><Select value={draft.broker} disabled={mode==='edit'} onChange={brokerId=>{const next=brokers.find(row=>row.id===brokerId)!;setDraft({...draft,broker:brokerId,brokerName:next.name});}}>{brokers.map(row=><option value={row.id} key={row.id}>{row.name}</option>)}</Select></Field></div>
    <fieldset><legend>Sessions</legend><div className="session-elements-grid"><table className="plain-table" aria-label="Session elements"><thead><tr>{['#','Start day','Start time','End day','End time','SEOC'].map(value=><th key={value}>{value}</th>)}</tr></thead><tbody>{draft.elements.map((row,index)=><tr key={`${index}-${row.dayFrom}-${row.timeFrom}`} className={selected===index?'selected':''} onClick={()=>setSelected(index)} onDoubleClick={()=>{setSelected(index);setElement({mode:'edit',index});}}><td>{index+1}</td><td>{row.dayFrom}</td><td>{row.timeFrom}</td><td>{row.dayTo}</td><td>{row.timeTo}</td><td>{row.eod?'Yes':'No'}</td></tr>)}{!draft.elements.length&&<tr><td colSpan={6} className="dataset-empty">No sessions defined.</td></tr>}</tbody></table></div>
      <div className="session-element-actions"><Button onClick={()=>setElement({mode:'add'})}>Add</Button><Button onClick={()=>{try{setDraft({...draft,elements:generateMondayFriday(draft.elements)});setError('');}catch(cause){setError(cause instanceof Error?cause.message:'Unable to generate sessions.');}}}>Add Mon-Fri</Button><Button onClick={()=>{const index=requireSelection();if(index!==null)setElement({mode:'edit',index});}}>Edit</Button><Button onClick={()=>{const index=requireSelection();if(index!==null){setDraft({...draft,elements:draft.elements.filter((_,row)=>row!==index)});setSelected(null);}}}>Remove</Button><span>Note: Session times are based on exchange</span></div>
    </fieldset>
  </Modal>
  {element&&<SessionElementDialog mode={element.mode} value={element.index===undefined?undefined:draft.elements[element.index]} onClose={()=>setElement(null)} onSave={saveElement}/>}
  {discard&&<Modal title="Changes not saved" width={470} onClose={()=>setDiscard(false)} footer={<><Button onClick={()=>setDiscard(false)}>No</Button><Button className="primary" onClick={onClose}>Yes</Button></>}><p>Do you really want to discard changes?</p></Modal>}
  </div>;
}
