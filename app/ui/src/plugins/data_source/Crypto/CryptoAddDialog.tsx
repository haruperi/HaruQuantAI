import { useEffect, useRef, useState, type ReactNode } from 'react';
import { Button, Modal, TextInput } from '../../../components/ui';
import { datasets } from '../Common/fixtures';
import { cryptoDefinitions, cryptoExchange, type CryptoExchangeId } from './crypto';
import { cryptoActive, reservedCrypto, useCrypto } from './cryptoStore';
import { useDataManagerStore, useDukascopyDownloads, useTickDownloader } from '../Common/dataManagerStore';
import { reservedDarwinex, useDarwinex } from '../Darwinex/darwinexStore';
import { activeImport, useFileImports } from '../FileImport/fileImportStore';
import { useFileSymbols } from '../FileImport/fileSymbolsStore';
import { reservedSQDefinitions, useSQData } from '../SQData/sqDataStore';
import { reservedYahoo, useYahoo } from '../Yahoo/yahooStore';
import { reservedMt5, useMt5Import } from '../MetaTrader/mt5ImportStore';
import './crypto.css';

export function cryptoContext() {
  const data = useDataManagerStore.getState(), td = useTickDownloader.getState(), files = useFileSymbols.getState(), imports = useFileImports.getState();
  const error = data.storageError || td.storageError || files.storageError || imports.storageError || useCrypto.getState().storageError || useYahoo.getState().storageError;
  if (error) throw new Error(error);
  const rows = [...datasets, ...data.definitions, ...td.definitions, ...files.definitions, ...imports.records, ...reservedSQDefinitions(), ...reservedDarwinex(), ...reservedCrypto(), ...reservedYahoo(), ...reservedMt5(), ...(activeImport(imports.job?.state) ? imports.job!.tasks.map(task => task.record) : [])];
  const active = [td.job?.state, imports.job?.state, useSQData.getState().job?.state, useMt5Import.getState().job?.state, useDukascopyDownloads.getState().job?.state, useDarwinex.getState().job?.state, useYahoo.getState().job?.state].some(cryptoActive);
  return { existing: rows.map(row => row.symbol), active };
}

export function CryptoModal({ title, onClose, children, footer, wide = false }: { title: string; onClose: () => void; children: ReactNode; footer: ReactNode; wide?: boolean }) {
  return <div className={`crypto-flow ${wide ? 'crypto-wide' : ''}`} onKeyDown={event => {
    if (event.key !== 'Tab') return;
    const controls = Array.from(event.currentTarget.querySelectorAll<HTMLElement>('button:not(:disabled),input:not(:disabled),select:not(:disabled),a[href]'));
    if (event.shiftKey && document.activeElement === controls[0]) { event.preventDefault(); controls.at(-1)?.focus(); }
    else if (!event.shiftKey && document.activeElement === controls.at(-1)) { event.preventDefault(); controls[0]?.focus(); }
  }}><Modal title={title} width={wide ? 900 : 720} onClose={onClose} footer={footer}>{children}</Modal></div>;
}

export function CryptoAddDialog({ exchangeId, onClose, onStarted }: { exchangeId: CryptoExchangeId; onClose: () => void; onStarted: () => void }) {
  const exchange = cryptoExchange(exchangeId), store = useCrypto();
  const [query, setQuery] = useState(''), [selected, setSelected] = useState<string[]>([]), [timeframe, setTimeframe] = useState(exchange.timeframes[0]), [postfix, setPostfix] = useState(''), [agreed, setAgreed] = useState(false), [error, setError] = useState('');
  const allCheck = useRef<HTMLInputElement>(null);
  const rows = exchange.symbols.filter(row => row.symbol.toLowerCase().includes(query.trim().toLowerCase()));
  const all = rows.length > 0 && rows.every(row => selected.includes(row.symbol));
  useEffect(() => { if (allCheck.current) allCheck.current.indeterminate = selected.length > 0 && !all; }, [all, selected]);
  function save() {
    try {
      if (!selected.length) throw new Error('No symbols selected');
      if (!agreed) throw new Error('Please read and confirm Data Disclaimer for Free Data.');
      const context = cryptoContext(), definitions = cryptoDefinitions(exchangeId, selected, timeframe, postfix, context.existing);
      store.startAdd(definitions, context.active); onStarted(); onClose();
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to add Crypto data.'); }
  }
  return <CryptoModal wide title={exchange.title} onClose={onClose} footer={<>
    <label className="crypto-consent"><input type="checkbox" checked={agreed} onChange={event => { setAgreed(event.target.checked); setError(''); }}/> I confirm that I understand the following: Data are provided for free by {exchange.menuLabel}. HaruQuantAI Data Manager is only a tool to download the data directly to the program. HaruQuantAI is not responsible for quality or availability of the data.</label>
    <Button onClick={onClose}>Close</Button><Button className="primary" onClick={save}>Save</Button>
  </>}>
    {(error || store.storageError) && <p className="crypto-error" role="alert">{error || store.storageError}</p>}
    <fieldset className="crypto-catalogue"><legend>Choose from available data</legend>
      <div className="crypto-filter"><TextInput aria-label="Filter items" placeholder="Filter items" value={query} onChange={event => { setQuery(event.target.value); setSelected([]); setError(''); }}/><span>{rows.length} mock symbols</span></div>
      <div className="crypto-grid"><table className="plain-table" aria-label={`${exchange.menuLabel} symbols`}><thead><tr><th><input ref={allCheck} type="checkbox" aria-label={`Select all ${exchange.menuLabel} symbols`} checked={all} disabled={!rows.length} onChange={() => setSelected(all ? [] : rows.map(row => row.symbol))}/></th><th>Symbol</th></tr></thead><tbody>{rows.map(row => <tr key={row.symbol} className={selected.includes(row.symbol) ? 'selected' : ''}><td><input type="checkbox" aria-label={`Select symbol ${row.symbol}`} checked={selected.includes(row.symbol)} onChange={() => setSelected(current => current.includes(row.symbol) ? current.filter(item => item !== row.symbol) : [...current, row.symbol])}/></td><td>{row.symbol}</td></tr>)}{!rows.length && <tr><td colSpan={2}>No symbols available.</td></tr>}</tbody></table></div>
      <div className="crypto-details"><label>Timeframe <select aria-label="Timeframe" value={timeframe} onChange={event => { setTimeframe(event.target.value); setError(''); }}>{exchange.timeframes.map(value => <option key={value}>{value}</option>)}</select></label><label>Data postfix <span><TextInput aria-label="Data postfix" maxLength={64} value={postfix} onChange={event => { setPostfix(event.target.value); setError(''); }}/><small>This postfix will be optionally added to the data names created</small></span></label></div>
      <p className="crypto-mock-note">Offline mock catalog. No exchange connection is made.</p>
    </fieldset>
  </CryptoModal>;
}
