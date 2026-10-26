import { useRef, useState } from 'react';
import { Button, Modal } from '../../../../components/ui';
import { loadStockGroupCatalog } from './stockGroupApiClient';
import { stockGroupLimits } from './stockGroups';
import { useStockGroups } from './stockGroupsStore';
import './stockGroups.css';
export function StockGroupTransferDialog({onClose,onSaved}:{onClose:()=>void;onSaved:(message:string)=>void}) {
  const [file,setFile]=useState<File|null>(null);const [error,setError]=useState('');const [pending,setPending]=useState(false);const busy=useRef(false);
  function close(){if(!busy.current)onClose();}
  async function load(){if(busy.current)return;busy.current=true;setPending(true);setError('');try{
    if(!file||file.size>stockGroupLimits.json)throw new Error('Choose a Groups JSON file up to 20 MiB.');
    const count=await loadStockGroupCatalog(await file.text());
    await useStockGroups.getState().syncRemote();
    if(useStockGroups.getState().storageError){setFile(null);throw new Error(`${count} groups loaded; catalog refresh failed. Close this dialog and retry the catalog refresh.`);}
    onSaved(`Groups (${count}) loaded.`);onClose();
  }catch(cause){setError(cause instanceof Error?cause.message:'Unable to load groups');}finally{busy.current=false;setPending(false);}}
  return <div className="stock-groups-flow"><Modal title="Load groups" width={620} onClose={close} footer={<><Button disabled={pending} onClick={close}>Close</Button><Button disabled={pending||!file} className="primary" onClick={()=>void load()}>{pending?'Loading…':'Load'}</Button></>}>
    {error&&<p role="alert" className="stock-group-error">{error}</p>}
    <label>Groups JSON file<input aria-label="Groups file" disabled={pending} type="file" accept=".json,application/json" onChange={event=>{setFile(event.target.files?.[0]??null);setError('');}}/></label>
    <p>Choose a JSON array exported by Save or the basket CLI. All groups and memberships load together. Existing names are rejected without changing the catalog.</p>
  </Modal></div>;
}
