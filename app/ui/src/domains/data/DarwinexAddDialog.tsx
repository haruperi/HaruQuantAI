import { useCallback, useRef, useState, type ReactNode } from 'react';
import { Button, Modal, TextInput } from '../../components/ui';
import { datasets } from '../../mocks/fixtures';
import { useDataManagerStore, useDukascopyDownloads, useTickDownloader } from './dataManagerStore';
import { useFileSymbols } from './fileSymbolsStore';
import { useFileImports } from './fileImportStore';
import { reservedSQDefinitions, useSQData } from './sqDataStore';
import { darwinexActive, reservedDarwinex, useDarwinex } from './darwinexStore';
import { reservedCrypto, useCrypto } from './cryptoStore';
import { reservedYahoo, useYahoo } from './yahooStore';
import { reservedMt5, useMt5Import } from './mt5ImportStore';
import { darwinexCatalogue, darwinexDefinitions } from './darwinex';
import './darwinex.css';
export function darwinexContext() {
  const data = useDataManagerStore.getState(), td = useTickDownloader.getState(), files = useFileSymbols.getState(), imports = useFileImports.getState();
  const error = data.storageError || td.storageError || files.storageError || imports.storageError;
  if (error) throw new Error(error);
  const rows = [...datasets, ...data.definitions, ...td.definitions, ...files.definitions, ...imports.records, ...reservedCrypto(), ...reservedYahoo(), ...reservedSQDefinitions(), ...reservedDarwinex(), ...reservedMt5(), ...(darwinexActive(imports.job?.state) ? imports.job!.tasks.map(task => task.record) : [])];
  return { existing: rows.map(row => row.symbol), active: [td.job?.state, imports.job?.state, useSQData.getState().job?.state, useMt5Import.getState().job?.state, useDukascopyDownloads.getState().job?.state, useCrypto.getState().job?.state, useYahoo.getState().job?.state].some(darwinexActive) };
}
export function DarwinexModal({ title, onClose, children, footer, wide = false }: { title: string; onClose: () => void; children: ReactNode; footer: ReactNode; wide?: boolean }) {
  return <div className={`darwinex-flow ${wide ? 'darwinex-wide' : ''}`} onKeyDown={event => {
    if (event.key !== 'Tab') return;
    const controls = Array.from(event.currentTarget.querySelectorAll<HTMLElement>('button:not(:disabled),input:not(:disabled):not([type=file]),select:not(:disabled),a[href]'));
    if (event.shiftKey && document.activeElement === controls[0]) { event.preventDefault(); controls.at(-1)?.focus(); }
    else if (!event.shiftKey && document.activeElement === controls.at(-1)) { event.preventDefault(); controls[0]?.focus(); }
  }}><Modal title={title} width={wide ? 900 : 720} onClose={onClose} footer={footer}>{children}</Modal></div>;
}
export function DarwinexAddDialog({ onClose, onStarted }: { onClose: () => void; onStarted: () => void }) {
  const data = useDataManagerStore(); const store = useDarwinex();
  const [query, setQuery] = useState(''), [selected, setSelected] = useState<string[]>([]), [brokerId, setBroker] = useState('-1'), [postfix, setPostfix] = useState(store.postfix), [agreed, setAgreed] = useState(false), [error, setError] = useState(''), [notice, setNotice] = useState('');
  const [mapping, setMapping] = useState(false), [mappings, setMappings] = useState<Record<string,string>>({});
  const [sort, setSort] = useState<'symbol' | 'dateFrom' | null>(null), [descending, setDescending] = useState(false); const warned = useRef(false);
  const broker = data.brokers.find(row => row.id === brokerId && row.mtUse);
  const rows = darwinexCatalogue.filter(row => row.symbol.toLowerCase().includes(query.toLowerCase())).sort((a,b) => sort ? a[sort].localeCompare(b[sort]) * (descending ? -1 : 1) : 0);
  const close = useCallback(() => { if (mapping) { setMapping(false); setError(''); } else onClose(); }, [mapping, onClose]);
  function save() {
    try {
      if (!selected.length) throw new Error('No symbols selected');
      if (!agreed) throw new Error('Please confirm that you understand the free data disclaimer.');
      if (brokerId !== '-1' && !broker) throw new Error('Choose a valid broker profile.');
      if (broker && !mapping) { setMappings(Object.fromEntries(selected.map(symbol => [symbol, broker.instruments.find(item => !item.startsWith('[') && item.startsWith(symbol)) ?? '-1001']))); setMapping(true); setError(''); return; }
      const context = darwinexContext(); const definitions = darwinexDefinitions(selected, postfix, context.existing, broker, mappings);
      if (!definitions.length) throw new Error('No symbols selected');
      store.start('add', definitions, context.active, undefined, postfix); onStarted(); onClose();
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to add data.'); }
  }
  function mass(value: string) { setMappings(current => Object.fromEntries(Object.entries(current).map(([symbol, mapping]) => [symbol, mapping === '-1001' ? value : mapping]))); }
  return <DarwinexModal key={mapping ? 'mapping' : 'add'} wide title={mapping ? 'Add Darwinex data - identify instruments' : 'Add Darwinex data'} onClose={close} footer={<>
    {!mapping && <label className="darwinex-consent"><input type="checkbox" checked={agreed} onChange={event => setAgreed(event.target.checked)}/> I confirm that I understand the following: Data are provided for free by Darwinex. HaruQuantAI Data Manager is only a tool to download the data directly to the program. HaruQuantAI is not responsible for quality or availability of the data.</label>}
    <Button onClick={close}>{mapping ? '< Back' : 'Close'}</Button><Button className="primary" onClick={save}>Save</Button>
  </>}>
    {(error || data.storageError || store.storageError) && <p role="alert" className="darwinex-error">{error || data.storageError || store.storageError}</p>}
    {mapping ? <fieldset><legend>You have chosen broker profile {broker?.name}</legend><p>Downloaded data will be recomputed to this broker timezone.</p><h3>Please select corresponding instrument for added data</h3><p>Select a corresponding broker profile instrument for every added symbol. If it is not defined, skip the symbol or use the Default instrument.</p><div className="darwinex-mass">Mass action: Set all unconfigured symbols to <Button onClick={() => mass('-1')}>Default instrument</Button><Button onClick={() => mass('-1000')}>Skip adding the symbol</Button></div><div className="darwinex-grid"><table className="plain-table"><thead><tr><th>Symbol</th><th>Instrument</th></tr></thead><tbody>{selected.map(symbol => <tr key={symbol}><td>{symbol}</td><td><select aria-label={`Instrument for ${symbol}`} value={mappings[symbol]} onChange={event => setMappings(current => ({ ...current, [symbol]: event.target.value }))}><option value="-1001">choose instrument</option>{broker?.instruments.filter(item => !item.startsWith('[')).map(item => <option key={item}>{item}</option>)}<option value="-1">Default</option><option value="-1000">Skip adding this symbol</option></select></td></tr>)}</tbody></table></div></fieldset> : <fieldset className="darwinex-catalogue"><legend>Choose from available data</legend>
    <TextInput aria-label="Filter items" placeholder="Filter items" value={query} onChange={event => { setQuery(event.target.value); setSelected([]); }}/>
    <div className="darwinex-grid"><table className="plain-table" aria-label="Available Darwinex data"><thead><tr><th><input type="checkbox" aria-label="Select all Darwinex symbols" checked={rows.length > 0 && rows.every(row => selected.includes(row.symbol))} disabled={!rows.length} onChange={() => setSelected(rows.every(row => selected.includes(row.symbol)) ? [] : rows.map(row => row.symbol))}/></th>{(['symbol','dateFrom'] as const).map(key => <th key={key} aria-sort={sort === key ? descending ? 'descending' : 'ascending' : 'none'}><button onClick={() => { setDescending(sort === key && !descending); setSort(key); }}>{key === 'symbol' ? 'Symbol' : 'Available data range'}</button></th>)}</tr></thead><tbody>{rows.map(row => <tr key={row.symbol} className={selected.includes(row.symbol) ? 'selected' : ''}><td><input type="checkbox" aria-label={`Select symbol ${row.symbol}`} checked={selected.includes(row.symbol)} onChange={() => setSelected(current => current.includes(row.symbol) ? current.filter(item => item !== row.symbol) : [...current,row.symbol])}/></td><td>{row.symbol}</td><td>from {row.dateFrom.replaceAll('-','.')}</td></tr>)}{!rows.length && <tr><td colSpan={3}>No Darwinex symbols available.</td></tr>}</tbody></table></div>
    <div className="darwinex-details"><label>Broker profile * <select aria-label="Broker profile" value={brokerId} onChange={event => { const id = event.target.value; setBroker(id); setPostfix(data.brokers.find(row => row.id === id)?.postfix ?? ''); if (id !== '-1' && !warned.current) { warned.current = true; setNotice("You have selected a non-default broker. Data will be automatically adjusted to the broker's time zone during download."); } }}><option value="-1">Default</option>{data.brokers.filter(row => row.mtUse).map(row => <option key={row.id} value={row.id}>{row.name}</option>)}</select></label><label>Data postfix <TextInput aria-label="Data postfix" maxLength={64} value={postfix} onChange={event => setPostfix(event.target.value)}/><small>This postfix will be optionally added to the data names created</small></label></div>{notice && <p role="status">{notice}</p>}
    </fieldset>}
  </DarwinexModal>;
}
