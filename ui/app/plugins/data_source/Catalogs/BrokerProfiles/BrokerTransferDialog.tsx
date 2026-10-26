import { useRef, useState } from 'react';
import { Button, Field, Modal } from '../../../../components/ui';
import { loadBrokerCatalog } from './brokerApiClient';
import { useDataManagerStore } from '../../Common/dataManagerStore';
import './brokerProfiles.css';

export function BrokerTransferDialog({onClose,onSaved}:{onClose:()=>void;onSaved:(message:string)=>void}) {
  const busy = useRef(false);
  const [pending,setPending] = useState(false);
  const [file,setFile] = useState<File|null>(null);
  const [error,setError] = useState('');
  function close() { if (!busy.current) onClose(); }
  async function load() {
    if (busy.current) return;
    busy.current=true;setPending(true);setError('');
    try {
      if (!file || file.size > 10_000_000) throw new Error('Choose a Brokers JSON file up to 10 MB.');
      const count = await loadBrokerCatalog(await file.text());
      await useDataManagerStore.getState().syncBrokers();
      if (useDataManagerStore.getState().brokerError) {
        setError(`${count} brokers loaded. Refresh failed; close this dialog and retry the catalog refresh.`);
        setFile(null);return;
      }
      onSaved(`Brokers (${count}) loaded.`);onClose();
    } catch (cause) {setError(cause instanceof Error?cause.message:'Cannot load brokers.');}
    finally {busy.current=false;setPending(false);}
  }
  return <div className="broker-flow"><Modal title="Load brokers" width={560} onClose={close} footer={<><Button disabled={pending} onClick={close}>Close</Button><Button disabled={pending||!file} className="primary" onClick={()=>void load()}>{pending?'Loading…':'Validate and load'}</Button></>}>
    {error&&<p className="broker-error" role="alert">{error}</p>}
    <Field label="Brokers file (JSON)"><input aria-label="Brokers file" type="file" accept=".json,application/json" disabled={pending} onChange={event=>{setFile(event.target.files?.[0]??null);setError('');}}/></Field>
    <p className="broker-note">Import a JSON array exported by Brokers Save or the CLI. All profiles are imported together. Existing names are rejected without changing the catalog.</p>
  </Modal></div>;
}
