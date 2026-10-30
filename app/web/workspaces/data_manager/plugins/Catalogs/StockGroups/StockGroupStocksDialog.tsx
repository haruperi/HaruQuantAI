import { useEffect, useRef, useState } from 'react';
import { Button, Modal } from '../../../../../common/components/ui';
import { formatStockLines, parseStockLines, stockGroupLimits, type StockGroupDefinition } from './stockGroups';
import { fetchStockGroupMembers, importStockGroupMembers, exportStockGroupMembers } from './stockGroupApiClient';
import { useStockGroups } from './stockGroupsStore';
import './stockGroups.css';

function download(name:string,text:string) {const url=URL.createObjectURL(new Blob([text],{type:'text/csv;charset=utf-8'}));const link=document.createElement('a');link.href=url;link.download=name;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
export function StockGroupStocksDialog({group,onClose,onSaved}:{group:StockGroupDefinition;onClose:()=>void;onSaved:(message:string)=>void}) {
  const [text,setText]=useState(formatStockLines(group.members));const [error,setError]=useState('');
  const [pending,setPending]=useState(false);const [loading,setLoading]=useState(true);const [loadFailed,setLoadFailed]=useState(false);
  const busy=useRef(false);const fileRef=useRef<HTMLInputElement>(null);
  useEffect(()=>{let current=true;void fetchStockGroupMembers(group.id).then(saved=>{if(current)setText(formatStockLines(saved.members));}).catch(cause=>{if(current){setError(cause instanceof Error?cause.message:'Unable to load stocks');setLoadFailed(true);}}).finally(()=>{if(current)setLoading(false);});return()=>{current=false;};},[group.id]);
  function close(){if(!busy.current)onClose();}
  async function work(action:()=>Promise<void>){if(busy.current)return;busy.current=true;setPending(true);setError('');try{await action();}catch(cause){setError(cause instanceof Error?cause.message:'Unable to save stocks');}finally{busy.current=false;setPending(false);}}
  async function read(file?:File){if(!file)return;await work(async()=>{if(file.size>stockGroupLimits.csv)throw new Error('Stock list exceeds 20 MiB.');await importStockGroupMembers(group.id,await file.text());await useStockGroups.getState().syncRemote();onSaved('Stocks were imported');onClose();});}
  const disabled=pending||loading||loadFailed;
  return <div className="stock-groups-flow"><Modal title={`Edit stocks ${group.name}`} width={700} onClose={close} footer={<><Button disabled={pending} onClick={close}>Close</Button><Button disabled={disabled||group.system} className="primary" onClick={()=>void work(async()=>{await useStockGroups.getState().replaceMembers(group.id,parseStockLines(text));onSaved('Stocks were saved.');onClose();})}>Save</Button></>}>
    {loading&&<p role="status">Loading stocks…</p>}{error&&<p role="alert" className="stock-group-error">{error}</p>}
    <p>One membership per line: Ticker;Date from;Date to. Dates are optional and use DD.MM.YYYY or Unix milliseconds.</p>
    <p>AAPL<br/>TSLA;01.12.2020<br/>AMZN;15.04.2007;30.05.2015</p>
    <div className="stock-group-file-actions"><Button disabled={disabled||group.system} onClick={()=>fileRef.current?.click()}>Import from file</Button><Button disabled={disabled} onClick={()=>void work(async()=>{download(`${group.name.replace(/[[\]]/g,'')}_stocks.csv`,await exportStockGroupMembers(group.id));onSaved('Stocks were exported');})}>Export to file</Button><input ref={fileRef} hidden type="file" accept=".csv,.txt,text/csv,text/plain" aria-label="Choose stocks CSV" onChange={event=>void read(event.target.files?.[0])}/></div>
    <textarea aria-label="Stocks" className="text-input stock-group-members" disabled={disabled||group.system} value={text} onChange={event=>{setText(event.target.value);setError('');}}/>
  </Modal></div>;
}
