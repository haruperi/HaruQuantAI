import { reservedDarwinex, useDarwinex } from '../Darwinex/darwinexStore';
import { reservedCrypto, useCrypto } from '../Crypto/cryptoStore';
import { reservedYahoo, useYahoo } from '../Yahoo/yahooStore';
import { useSQData, reservedSQDefinitions } from '../SQData/sqDataStore';
import { reservedMt5, useMt5Import } from '../MetaTrader/mt5ImportStore';
import { useCallback, useRef, useState } from 'react';
import { Button, Field, TextInput } from '../../../components/ui';
import { datasets } from '../../../mocks/fixtures';
import { FileSymbolDialog } from './FileSymbolDialog';
import { useDataManagerStore, useDukascopyDownloads, useTickDownloader } from '../Common/dataManagerStore';
import { useFileSymbols } from './fileSymbolsStore';
import { activeImport, useFileImports } from './fileImportStore';
import { datePatterns, emptyFileRecord, importedRecord, limits, massSymbol, parseImport, readImportFile, timeframes, timezones, type ImportTask } from './fileImport';
import type { FileDefinition, FileInstrument } from './fileSymbols';
import './fileImport.css';

export function FileMassImportDialog({ onClose, onStarted }: { onClose: () => void; onStarted: () => void }) {
  const store = useFileImports(); const picker = useRef<HTMLInputElement>(null);
  const [files, setFiles] = useState<File[]>([]); const [folder, setFolder] = useState(''); const [error, setError] = useState(''); const [busy, setBusy] = useState(false);
  const cancelled = useRef(false);
  const close = useCallback(() => { cancelled.current = true; onClose(); }, [onClose]);
  const [timezone, setTimezone] = useState('EETUS'); const [timeframe, setTimeframe] = useState('D1'); const [dateFormat, setDateFormat] = useState('ddMMyyyy');
  const [group, setGroup] = useState(false); const [policy, setPolicy] = useState<'overwrite' | 'skip' | 'create'>('overwrite'); const [postfix, setPostfix] = useState('');
  async function start(instrument: FileInstrument, barType: 'start' | 'end') {
    if (!files.length) throw new Error('Choose a source data folder.');
    if (files.length > limits.files || files.reduce((n, file) => n + file.size, 0) > limits.folder) throw new Error('Folder limit: 500 files / 50 MiB.');
    const data = useDataManagerStore.getState(), td = useTickDownloader.getState(), symbols = useFileSymbols.getState();
    if (data.storageError || td.storageError || symbols.storageError) throw new Error(data.storageError || td.storageError || symbols.storageError);
    const existing = [...reservedYahoo(), ...reservedCrypto(), ...reservedDarwinex(), ...reservedSQDefinitions(), ...reservedMt5(), ...datasets, ...data.definitions, ...td.definitions, ...symbols.definitions, ...store.records];
    const tasks: ImportTask[] = []; const seen = new Set<string>(); let skipped = 0;
    setBusy(true); setError('');
    try {
      for (const file of files) {
        if (cancelled.current) return false;
        const stem = file.name.replace(/\.[^.]+$/, '');
        if (seen.has(stem) && policy !== 'create') throw new Error(`Multiple files use the name ${stem}; choose Create new ticker or select an unambiguous folder.`);
        seen.add(stem);
        const symbol = massSymbol(stem, postfix, existing, policy); if (!symbol) { skipped++; continue; }
        const text = await readImportFile(file);
        const parsed = parseImport(text, { name: 'Folder CSV', separator: ',', skipRows: 0, skipColumns: 0, dateFormat, columns: timeframe === 'TICK' ? ['Date & Time', 'Ask', 'Bid', 'Volume'] : ['Date', 'Open', 'High', 'Low', 'Close', 'Volume'] }, timeframe, false);
        const previous = existing.find(row => row.symbol === symbol);
        const base: FileDefinition = { ...emptyFileRecord(symbol, instrument, barType), id: previous?.id ?? `file:${symbol}` };
        tasks.push({ filename: file.name, record: importedRecord(base, parsed, timezone, undefined, true), ignored: parsed.ignored, error: parsed.error });
        existing.push(base);
      }
      if (cancelled.current) return false;
      useFileImports.getState().start(tasks, timezone, group ? folder || 'Imported symbols' : '', skipped, [useYahoo.getState().job?.state, useCrypto.getState().job?.state, useDarwinex.getState().job?.state, useSQData.getState().job?.state, useMt5Import.getState().job?.state, useDukascopyDownloads.getState().job?.state, useTickDownloader.getState().job?.state].some(activeImport));
      return true;
    } finally { setBusy(false); }
  }
  return <FileSymbolDialog onClose={close} onSaved={onStarted} mass={{ busy, onSave: start, postfix: <Field label="Data postfix"><TextInput value={postfix} maxLength={100} onChange={event => setPostfix(event.target.value)}/></Field>, content: <>
    {(error || store.storageError) && <p role="alert">{error || store.storageError}</p>}
    <fieldset><div className="import-file-picker"><Field label="Source data folder"><TextInput readOnly value={folder}/></Field><Button disabled={busy} onClick={() => picker.current?.click()}>Select</Button><input hidden ref={picker} aria-label="Choose source folder" type="file" multiple {...{ webkitdirectory: '', directory: '' }} onChange={event => {
      const chosen = Array.from(event.target.files ?? []).sort((a, b) => (a.webkitRelativePath || a.name).localeCompare(b.webkitRelativePath || b.name));
      setFiles(chosen); setFolder(chosen[0]?.webkitRelativePath.split('/')[0] || (chosen.length ? 'Selected files' : '')); setError('');
    }}/></div>{files.length > 0 && <small>{files.length} files selected</small>}
      <div className="import-grid"><Field label="Imported data timezone"><select aria-label="Imported data timezone" value={timezone} onChange={event => setTimezone(event.target.value)}>{timezones.map(([id, label]) => <option key={label} value={id}>{label}</option>)}</select></Field><Field label="Imported timeframe"><select aria-label="Imported timeframe" value={timeframe} onChange={event => setTimeframe(event.target.value)}>{timeframes.map(value => <option key={value}>{value}</option>)}</select></Field><Field label="Date format"><TextInput list="mass-date-patterns" value={dateFormat} onChange={event => setDateFormat(event.target.value)}/></Field><datalist id="mass-date-patterns">{datePatterns.map(pattern => <option key={pattern}>{pattern}</option>)}</datalist></div>
      <label><input type="checkbox" checked={group} onChange={event => setGroup(event.target.checked)}/> Create a new stockgroup from imported symbols</label>
      <div className="import-grid"><fieldset><legend>Folder/File csv format</legend><label><input type="radio" checked readOnly/> Date,Open,High,Low,Close,Volume<br/>Date,Ask,Bid,Volume - in case of tick timeframes</label></fieldset><fieldset className="import-mass-options"><legend>If data already exists</legend>{([['overwrite', 'Overwrite'], ['skip', 'Skip'], ['create', 'Create new ticker in data - adds postfix 2 or 3 etc.']] as const).map(([value, label]) => <label key={value}><input type="radio" checked={policy === value} onChange={() => setPolicy(value)}/> {label}</label>)}</fieldset></div>
    </fieldset>
  </> }}/ >;
}
