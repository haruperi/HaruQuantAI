import { useCallback, useRef, useState } from 'react';
import { Button, Field, Modal, TextInput } from '../../../components/ui';
import { activeImport, useFileImports } from './fileImportStore';
import { datePatterns, emptyFileRecord, importedRecord, limits, massSymbol, parseImport, readImportFile, timeframes, timezones, type ImportTask } from './fileImport';
import { newInstrument, type FileDefinition, type FileInstrument } from './presentation';
import './fileImport.css';

export interface FileMassImportContextDocument {
  readonly existing: readonly string[];
  readonly active: boolean;
  readonly error?: string;
  readonly instruments?: readonly FileInstrument[];
}

export function FileMassImportDialog({
  contextDocument,
  onClose,
  onStarted,
}: {
  contextDocument?: FileMassImportContextDocument;
  onClose: () => void;
  onStarted: () => void;
}) {
  const store = useFileImports();
  const picker = useRef<HTMLInputElement>(null);
  const [files, setFiles] = useState<File[]>([]);
  const [folder, setFolder] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const cancelled = useRef(false);
  const close = useCallback(() => { cancelled.current = true; onClose(); }, [onClose]);
  const [timezone, setTimezone] = useState('EETUS');
  const [timeframe, setTimeframe] = useState('D1');
  const [dateFormat, setDateFormat] = useState('ddMMyyyy');
  const [group, setGroup] = useState(false);
  const [policy, setPolicy] = useState<'overwrite' | 'skip' | 'create'>('overwrite');
  const [postfix, setPostfix] = useState('');
  const [barType, setBarType] = useState<'start' | 'end'>('start');

  const availableInstruments = (contextDocument?.instruments && contextDocument.instruments.length > 0)
    ? contextDocument.instruments
    : [newInstrument()];
  const [selectedInstrumentSymbol, setSelectedInstrumentSymbol] = useState(availableInstruments[0]?.symbol ?? 'EURUSD');
  const selectedInstrument = availableInstruments.find(item => item.symbol === selectedInstrumentSymbol) ?? availableInstruments[0] ?? newInstrument();

  async function start(instrument: FileInstrument, selectedBarType: 'start' | 'end') {
    if (!files.length) { setError('Choose a source data folder.'); return; }
    if (files.length > limits.files || files.reduce((n, file) => n + file.size, 0) > limits.folder) {
      setError('Folder limit: 500 files / 50 MiB.');
      return;
    }
    if (contextDocument?.error) { setError(contextDocument.error); return; }
    const existing = [...(contextDocument?.existing ?? []), ...store.records.map(r => r.symbol)];
    const tasks: ImportTask[] = [];
    const seen = new Set<string>();
    let skipped = 0;
    setBusy(true);
    setError('');
    try {
      for (const file of files) {
        if (cancelled.current) return;
        const stem = file.name.replace(/\.[^.]+$/, '');
        if (seen.has(stem) && policy !== 'create') {
          throw new Error(`Multiple files use the name ${stem}; choose Create new ticker or select an unambiguous folder.`);
        }
        seen.add(stem);
        const symbol = massSymbol(stem, postfix, existing.map(s => ({ symbol: s, source: 'File import' })), policy);
        if (!symbol) { skipped++; continue; }
        const text = await readImportFile(file);
        const parsed = parseImport(text, { name: 'Folder CSV', separator: ',', skipRows: 0, skipColumns: 0, dateFormat, columns: timeframe === 'TICK' ? ['Date & Time', 'Ask', 'Bid', 'Volume'] : ['Date', 'Open', 'High', 'Low', 'Close', 'Volume'] }, timeframe, false);
        const previousId = `file:${symbol}`;
        const base: FileDefinition = { ...emptyFileRecord(symbol, instrument, selectedBarType), id: previousId };
        tasks.push({ filename: file.name, record: importedRecord(base, parsed, timezone, undefined, true), ignored: parsed.ignored, error: parsed.error });
        existing.push(symbol);
      }
      if (cancelled.current) return;
      useFileImports.getState().start(
        tasks,
        timezone,
        group ? folder || 'Imported symbols' : '',
        skipped,
        contextDocument?.active ?? false,
      );
      onStarted();
      onClose();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Unable to import files.');
    } finally {
      setBusy(false);
    }
  }

  return <div className="file-import-flow" onKeyDown={event => {
    if (event.key !== 'Tab') return;
    const controls = Array.from(event.currentTarget.querySelectorAll<HTMLElement>('button:not(:disabled),input:not(:disabled):not([type=file]),select:not(:disabled)'));
    if (event.shiftKey && document.activeElement === controls[0]) { event.preventDefault(); controls.at(-1)?.focus(); }
    else if (!event.shiftKey && document.activeElement === controls.at(-1)) { event.preventDefault(); controls[0]?.focus(); }
  }}>
    <Modal title="Mass import" width={990} onClose={close} footer={<>
      <Button onClick={close}>Close</Button>
      <Button className="primary" disabled={busy} onClick={() => start(selectedInstrument, barType)}>{busy ? 'Reading…' : 'Save'}</Button>
    </>}>
      {(error || store.storageError || contextDocument?.error) && <p role="alert" className="file-symbol-error">{error || store.storageError || contextDocument?.error}</p>}
      <fieldset><div className="import-file-picker"><Field label="Source data folder"><TextInput readOnly value={folder}/></Field><Button disabled={busy} onClick={() => picker.current?.click()}>Select</Button><input hidden ref={picker} aria-label="Choose source folder" type="file" multiple {...{ webkitdirectory: '', directory: '' }} onChange={event => {
        const chosen = Array.from(event.target.files ?? []).sort((a, b) => (a.webkitRelativePath || a.name).localeCompare(b.webkitRelativePath || b.name));
        setFiles(chosen); setFolder(chosen[0]?.webkitRelativePath.split('/')[0] || (chosen.length ? 'Selected files' : '')); setError('');
      }}/></div>{files.length > 0 && <small>{files.length} files selected</small>}
        <div className="import-grid"><Field label="Imported data timezone"><select aria-label="Imported data timezone" value={timezone} onChange={event => setTimezone(event.target.value)}>{timezones.map(([id, label]) => <option key={label} value={id}>{label}</option>)}</select></Field><Field label="Imported timeframe"><select aria-label="Imported timeframe" value={timeframe} onChange={event => setTimeframe(event.target.value)}>{timeframes.map(value => <option key={value}>{value}</option>)}</select></Field><Field label="Date format"><TextInput list="mass-date-patterns" value={dateFormat} onChange={event => setDateFormat(event.target.value)}/></Field><datalist id="mass-date-patterns">{datePatterns.map(pattern => <option key={pattern}>{pattern}</option>)}</datalist></div>
        <label><input type="checkbox" checked={group} onChange={event => setGroup(event.target.checked)}/> Create a new stockgroup from imported symbols</label>
        <div className="import-grid"><fieldset><legend>Folder/File csv format</legend><label><input type="radio" checked readOnly/> Date,Open,High,Low,Close,Volume<br/>Date,Ask,Bid,Volume - in case of tick timeframes</label></fieldset><fieldset className="import-mass-options"><legend>If data already exists</legend>{([['overwrite', 'Overwrite'], ['skip', 'Skip'], ['create', 'Create new ticker in data - adds postfix 2 or 3 etc.']] as const).map(([value, label]) => <label key={value}><input type="radio" checked={policy === value} onChange={() => setPolicy(value)}/> {label}</label>)}</fieldset></div>
      </fieldset>
      <fieldset><legend>Data type</legend>
        <div className="import-bar-postfix">
          <div>
            <div className="file-symbol-radios">
              <label><input type="radio" name="file-bar-type" checked={barType === 'start'} onChange={() => setBarType('start')}/> Timestamp is start of bar time (MetaTrader, Dukascopy, forex data)</label>
              <label><input type="radio" name="file-bar-type" checked={barType === 'end'} onChange={() => setBarType('end')}/> Timestamp is end of bar time (NinjaTrader, Tradestation, futures data)</label>
            </div>
          </div>
          <Field label="Data postfix"><TextInput value={postfix} maxLength={100} onChange={event => setPostfix(event.target.value)}/></Field>
        </div>
      </fieldset>
      <fieldset><legend>Choose instrument</legend>
        <p>Instrument is a specification of this symbol - it contains tick size, point value etc.</p>
        <p>You can have multiple data imported - for example EURUSD_1, EURUSD_2, EURUSD_3, but they share the same instrument specification for EURUSD.</p>
        <div className="file-symbol-chooser">
          <Field label="Instrument">
            <select aria-label="Instrument" value={selectedInstrumentSymbol} onChange={event => setSelectedInstrumentSymbol(event.target.value)}>
              {availableInstruments.map(row => <option key={row.symbol} value={row.symbol}>{row.symbol}</option>)}
            </select>
          </Field>
        </div>
      </fieldset>
    </Modal>
  </div>;
}
