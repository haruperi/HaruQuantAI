import { useState, type ReactNode } from 'react';
import { Button, Modal, TextInput } from '../../../components/ui';
import { datasets } from '../../../mocks/fixtures';
import { reservedCrypto, useCrypto } from '../Crypto/cryptoStore';
import { useDataManagerStore, useDukascopyDownloads, useTickDownloader } from '../Common/dataManagerStore';
import { reservedDarwinex, useDarwinex } from '../Darwinex/darwinexStore';
import { activeImport, useFileImports } from '../FileImport/fileImportStore';
import { useFileSymbols } from '../FileImport/fileSymbolsStore';
import { reservedSQDefinitions, useSQData } from '../SQData/sqDataStore';
import { yahooDefinitions } from './yahoo';
import { reservedYahoo, useYahoo, yahooActive } from './yahooStore';
import { reservedMt5, useMt5Import } from '../MetaTrader/mt5ImportStore';
import './yahoo.css';

export function yahooContext() {
  const data = useDataManagerStore.getState(), td = useTickDownloader.getState(), files = useFileSymbols.getState(), imports = useFileImports.getState(), yahoo = useYahoo.getState();
  const error = data.storageError || td.storageError || files.storageError || imports.storageError || yahoo.storageError;
  if (error) throw new Error(error);
  const rows = [...datasets, ...data.definitions, ...td.definitions, ...files.definitions, ...imports.records, ...reservedSQDefinitions(), ...reservedDarwinex(), ...reservedCrypto(), ...reservedYahoo(), ...reservedMt5(), ...(activeImport(imports.job?.state) ? imports.job!.tasks.map(task => task.record) : [])];
  const active = [td.job?.state, imports.job?.state, useSQData.getState().job?.state, useMt5Import.getState().job?.state, useDukascopyDownloads.getState().job?.state, useDarwinex.getState().job?.state, useCrypto.getState().job?.state].some(yahooActive);
  return { existing: rows.map(row => row.symbol), active };
}

export function YahooModal({ title, onClose, children, footer, wide = false }: { title: string; onClose: () => void; children: ReactNode; footer: ReactNode; wide?: boolean }) {
  return <div className={`yahoo-flow ${wide ? 'yahoo-wide' : ''}`} onKeyDown={event => {
    if (event.key !== 'Tab') return;
    const controls = Array.from(event.currentTarget.querySelectorAll<HTMLElement>('button:not(:disabled),input:not(:disabled),textarea:not(:disabled),a[href]'));
    if (event.shiftKey && document.activeElement === controls[0]) { event.preventDefault(); controls.at(-1)?.focus(); }
    else if (!event.shiftKey && document.activeElement === controls.at(-1)) { event.preventDefault(); controls[0]?.focus(); }
  }}><Modal title={title} width={wide ? 900 : 720} onClose={onClose} footer={footer}>{children}</Modal></div>;
}

export function YahooAddDialog({ onClose, onStarted }: { onClose: () => void; onStarted: () => void }) {
  const store = useYahoo(); const [symbols, setSymbols] = useState(''), [postfix, setPostfix] = useState(''), [error, setError] = useState('');
  function save() { try { const context = yahooContext(); store.startAdd(yahooDefinitions(symbols, postfix, context.existing), context.active); onStarted(); onClose(); } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to add Yahoo data.'); } }
  return <YahooModal wide title="Add Yahoo data" onClose={onClose} footer={<><Button onClick={onClose}>Close</Button><Button className="primary" onClick={save}>Save</Button></>}>
    {(error || store.storageError) && <p className="yahoo-error" role="alert">{error || store.storageError}</p>}
    <fieldset className="yahoo-add-fieldset"><legend>Add data to download</legend>
      <div className="yahoo-help"><p>Please enter a list of stocks tickers you want to add, separated by comma, semicolon or newline.</p><p>For example: AAPL, AMZN, TSLA</p></div>
      <textarea aria-label="Yahoo symbols" value={symbols} onChange={event => { setSymbols(event.target.value); setError(''); }} />
    </fieldset>
    <label className="yahoo-postfix">Data postfix <span><TextInput aria-label="Data postfix" maxLength={64} value={postfix} onChange={event => { setPostfix(event.target.value); setError(''); }}/><small>This postfix will be optionally added to the data names created</small></span></label>
    <p className="yahoo-mock-note">Offline mock lookup. No request is sent to Yahoo Finance.</p>
  </YahooModal>;
}
