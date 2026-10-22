import { useState } from 'react';
import { Button, Field, Modal, TextInput } from '../../../../components/ui';
import { serializeSessionsJson, type SessionDefinition, type SessionBroker } from './sessions';
import './sessions.css';

export function SessionTransferDialog({ mode, selected, onClose, onSaved }: {
  mode: 'save' | 'load'; selected: SessionDefinition[]; all: SessionDefinition[]; brokers: SessionBroker[];
  onClose: () => void; onSaved: (message: string) => void;
}) {
  const [filename,setFilename] = useState('Sessions.json');
  const [error,setError] = useState('');
  function save() {
    try {
      if (mode !== 'save') throw new Error('Session import is not implemented.');
      if (!selected.length) throw new Error('Select sessions to export.');
      const url=URL.createObjectURL(new Blob([serializeSessionsJson(selected)],{type:'application/json'}));
      const anchor=document.createElement('a');anchor.href=url;anchor.download=/^[^\\/:*?"<>|]+\.json$/i.test(filename)?filename:'Sessions.json';
      anchor.click();window.setTimeout(()=>URL.revokeObjectURL(url),1000);onSaved('Sessions exported.');onClose();
    } catch(cause) {setError(cause instanceof Error?cause.message:'Unable to export sessions.');}
  }
  return <div className="sessions-flow"><Modal title={mode==='save'?'Save sessions':'Load sessions'} width={560} onClose={onClose} footer={<><Button onClick={onClose}>Close</Button>{mode==='save'&&<Button onClick={save}>Download JSON</Button>}</>}>
    {error&&<p role="alert">{error}</p>}{mode==='save'?<><p>Export complete configured profiles, intervals and holidays.</p><Field label="File name"><TextInput value={filename} onChange={event=>setFilename(event.target.value)}/></Field></>:<p>Session import is not implemented.</p>}
  </Modal></div>;
}
