import { useRef, useState } from 'react';
import { Button, Field, Modal, TextInput } from '../../../../components/ui';
import { parseInstrumentsJson, type FileInstrument } from '../../FileImport/fileSymbols';
import { parseSessionsJson, type SessionDefinition } from '../Sessions/sessions';
import { fromFileInstrument } from '../Instruments/instrumentsApiClient';
import { fromSessionDefinition } from '../Sessions/sessionApiClient';
import { useInstruments } from '../Instruments/instrumentsStore';
import { useSessions } from '../Sessions/sessionStore';
import { useDataManagerStore } from '../../Common/dataManagerStore';
import { importBrokerRecords, type BrokerImportResult } from './brokerApiClient';
import type { BrokerProfile } from './brokerProfiles';
import './brokerProfiles.css';

export function BrokerRecordImportDialog({kind,brokers,onClose,onSaved}:{kind:'instrument'|'session';brokers:BrokerProfile[];onClose:()=>void;onSaved:(message:string)=>void}) {
  const [fileName,setFileName] = useState('');
  const [rows,setRows] = useState<Array<FileInstrument | SessionDefinition>>([]);
  const [selected,setSelected] = useState<string[]>([]);
  const [brokerId,setBrokerId] = useState('-1');
  const [postfix,setPostfix] = useState('');
  const [overwrite,setOverwrite] = useState(false);
  const [useCosts,setUseCosts] = useState(false);
  const [pending,setPending] = useState(false);
  const [error,setError] = useState('');
  const [result,setResult] = useState<BrokerImportResult | null>(null);
  const busy = useRef(false);
  const browseVersion = useRef(0);
  const names = rows.map(row => 'symbol' in row ? row.symbol : row.name);
  const choices = [{id:'-1',name:'Default',postfix:'',timezone:'UTC'},...brokers.filter(row => row.mtUse && !row.system)];
  function close() { if (!busy.current) { browseVersion.current++; onClose(); } }
  async function browse(file: File | undefined) {
    const version = ++browseVersion.current;
    setRows([]);setSelected([]);setResult(null);setError('');setFileName('');setOverwrite(false);
    if (!file) return;
    try {
      if (file.size > 2_000_000) throw new Error('JSON file exceeds 2 MB.');
      const text = await file.text();
      const parsed = kind === 'instrument' ? parseInstrumentsJson(text,choices) : parseSessionsJson(text);
      if (!parsed.length) throw new Error('No records found in JSON file.');
      if (version !== browseVersion.current) return;
      setRows(parsed);setFileName(file.name);
    } catch (cause) { if (version === browseVersion.current) setError(cause instanceof Error ? cause.message : 'Cannot read JSON file.'); }
  }
  async function start() {
    if (busy.current) return;
    setError('');setResult(null);
    if (!selected.length) {setError('Select at least one record to import.');return;}
    busy.current = true;setPending(true);
    try {
      const records = rows.map(row => kind === 'instrument'
        ? fromFileInstrument({...row as FileInstrument,broker:brokerId})
        : fromSessionDefinition({...row as SessionDefinition,id:undefined,broker:brokerId}));
      const saved = await importBrokerRecords(kind,brokerId,records,{selected_names:selected,postfix,conflict_policy:overwrite?'overwrite':'error',use_profile_costs:useCosts});
      setResult(saved);
      const refresh = kind === 'instrument' ? useInstruments.getState().refreshFromServer() : useSessions.getState().refreshFromServer();
      await Promise.all([refresh,useDataManagerStore.getState().syncBrokers()]);
      const refreshError = kind === 'instrument' ? useInstruments.getState().error : useSessions.getState().error;
      const brokerError = useDataManagerStore.getState().brokerError;
      if (refreshError || brokerError) throw new Error(`Import result saved below; catalog refresh failed: ${refreshError || brokerError}`);
      const savedNames = new Set(saved.records.map(row => String(row[kind === 'instrument' ? 'symbol' : 'name'])));
      setSelected(current => current.filter(name => !savedNames.has(name+postfix)));
      if (!saved.failed.length && !saved.unattempted.length) {
        onSaved(`${saved.imported_count} ${kind} records imported.`);onClose();
      }
    } catch (cause) {setError(cause instanceof Error ? cause.message : 'Import could not be confirmed. Refresh catalogs before retrying.');}
    finally {busy.current=false;setPending(false);}
  }
  return <div className="broker-flow"><Modal title={kind === 'instrument' ? 'Instruments import from JSON' : 'Session import from JSON'} width={730} onClose={close} footer={<><Button disabled={pending} onClick={close}>Close</Button><Button disabled={pending || !rows.length} className="primary" onClick={() => void start()}>{pending ? 'Importingâ€¦' : 'Start Import'}</Button></>}>
    {error && <p className="broker-error" role="alert">{error}</p>}
    {result && <div role="status"><p>{result.imported_count} saved; {result.failed.length} failed; {result.unattempted.length} not attempted.</p>{result.failed.map(row => <p key={row.name}>{row.name}: {row.reason}</p>)}{result.unattempted.length > 0 && <p>Not attempted: {result.unattempted.join(', ')}</p>}</div>}
    <fieldset disabled={pending}><legend>Choose JSON file</legend><Field label="Data file"><div className="broker-file"><TextInput readOnly value={fileName}/><label className="button">Browse<input aria-label={`${kind} JSON file`} hidden type="file" accept=".json,application/json" onChange={e => void browse(e.target.files?.[0])}/></label></div></Field>
      <Field label="Broker profile"><select aria-label="Import broker profile" value={brokerId} onChange={e => {setBrokerId(e.target.value);setPostfix(choices.find(row => row.id === e.target.value)?.postfix ?? '');setOverwrite(false);setResult(null);}}>{choices.map(row => <option key={row.id} value={row.id}>{row.name}</option>)}</select></Field>
      <Field label="Postfix"><TextInput aria-label="Import postfix" maxLength={100} value={postfix} onChange={e => {setPostfix(e.target.value);setOverwrite(false);}}/></Field>
      <label className="broker-check"><input aria-label="Overwrite existing records" type="checkbox" checked={overwrite} onChange={e => setOverwrite(e.target.checked)}/>Overwrite matching records belonging to this broker</label>
      {kind === 'instrument' && <label className="broker-check"><input aria-label="Use broker cost defaults" type="checkbox" checked={useCosts} onChange={e => setUseCosts(e.target.checked)}/>Use configured broker spread and commission defaults</label>}
      <p className="broker-note">Each record saves separately. Any failed records stay visible for correction. A postfix is appended once to the file name.</p>
      <div className="broker-overview"><table className="plain-table"><thead><tr><th><input aria-label="Select all import records" type="checkbox" checked={names.length>0 && selected.length===names.length} onChange={() => setSelected(selected.length===names.length?[]:names)}/></th><th>Name</th><th>Target</th></tr></thead><tbody>{names.map(name => <tr key={name}><td><input aria-label={`Select ${name}`} type="checkbox" checked={selected.includes(name)} onChange={() => setSelected(selected.includes(name)?selected.filter(item => item!==name):[...selected,name])}/></td><td>{name}</td><td>{name+postfix}</td></tr>)}</tbody></table></div>
    </fieldset>
  </Modal></div>;
}
