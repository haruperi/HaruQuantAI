import { useDarwinex } from './darwinexStore';
import { useCrypto } from './cryptoStore';
import { useYahoo } from './yahooStore';
import { useSQData } from './sqDataStore';
import { useMt5Import } from './mt5ImportStore';
import { useCallback, useMemo, useRef, useState } from 'react';
import { Button, Field, Modal, TextInput } from '../../components/ui';
import { activeImport, useFileImports } from './fileImportStore';
import { useDukascopyDownloads, useTickDownloader } from './dataManagerStore';
import { builtInFormats, columnTypes, customFormat, dateExample, datePatterns, detectFormat, importedRecord, parseImport, previewRows, readImportFile, timeframes, timezones, type ColumnType, type ImportFormat } from './fileImport';
import type { FileDefinition } from './fileSymbols';
import './fileImport.css';

export function FileImportDialog({ target, onClose, onStarted }: { target: FileDefinition; onClose: () => void; onStarted: () => void }) {
  const store = useFileImports();
  const [format, setFormat] = useState(customFormat);
  const [timezone, setTimezone] = useState(store.timezone);
  const [timeframe, setTimeframe] = useState('auto');
  const [ignore, setIgnore] = useState(false);
  const [text, setText] = useState(''); const [filename, setFilename] = useState('');
  const [error, setError] = useState(''); const [busy, setBusy] = useState(false);
  const [page, setPage] = useState<'main' | 'save' | 'delete'>('main'); const [name, setName] = useState('');
  const picker = useRef<HTMLInputElement>(null); const generation = useRef(0);
  const formats = [customFormat(), ...builtInFormats, ...store.formats];
  const preview = useMemo(() => { try { const rows = text ? previewRows(text, format) : []; return { rows: rows.slice(0, 50), count: rows.length, error: '' }; } catch (cause) { return { rows: [], count: 0, error: String(cause) }; } }, [text, format]);
  const width = Math.max(format.columns.length, ...preview.rows.map(row => row.length), 0);
  const close = useCallback(() => { if (page !== 'main') { setPage('main'); setError(''); } else { generation.current++; onClose(); } }, [page, onClose]);
  function change(patch: Partial<ImportFormat>) { setFormat(current => ({ ...current, ...patch })); }
  function start() {
    try {
      if (!filename) throw new Error('Choose a data file.');
      if (preview.error) throw new Error(preview.error);
      const mapped = { ...format, columns: Array.from({ length: width }, (_, i) => format.columns[i] ?? '') };
      const result = parseImport(text, mapped, timeframe, ignore);
      const record = importedRecord(target, result, timezone, store.records.find(row => row.id === target.id));
      store.start([{ filename, record, ignored: result.ignored, error: result.error }], timezone, '', 0, [useYahoo.getState().job?.state, useCrypto.getState().job?.state, useDarwinex.getState().job?.state, useSQData.getState().job?.state, useMt5Import.getState().job?.state, useDukascopyDownloads.getState().job?.state, useTickDownloader.getState().job?.state].some(activeImport));
      onStarted(); onClose();
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to import file.'); }
  }
  function saveFormat(asNew: boolean) {
    try { if (asNew || format.name === 'Custom') { setName(''); setPage('save'); setError(''); return; } store.saveFormat(format, true); setError(''); }
    catch (cause) { setError(String(cause)); }
  }
  return <div className="file-import-flow" onKeyDown={event => {
    if (event.key !== 'Tab') return;
    const controls = Array.from(event.currentTarget.querySelectorAll<HTMLElement>('button:not(:disabled),input:not(:disabled):not([type=file]),select:not(:disabled)'));
    if (event.shiftKey && document.activeElement === controls[0]) { event.preventDefault(); controls.at(-1)?.focus(); }
    else if (!event.shiftKey && document.activeElement === controls.at(-1)) { event.preventDefault(); controls[0]?.focus(); }
  }}><Modal key={page} title={page === 'save' ? 'New data format' : page === 'delete' ? 'Delete data format' : `Data import for '${target.symbol}'`} width={page === 'main' ? 754 : 440} onClose={close} footer={<><Button onClick={close}>Close</Button><Button className="primary" disabled={busy} onClick={() => {
    if (page === 'main') start();
    else try { if (page === 'save') { store.saveFormat({ ...format, name }); change({ name: name.trim(), predefined: false }); } else { store.deleteFormat(format.name); change({ name: 'Custom', predefined: false }); } setPage('main'); setError(''); } catch (cause) { setError(String(cause)); }
  }}>{page === 'main' ? busy ? 'Reading…' : 'Start Import' : page === 'save' ? 'Save' : 'Delete'}</Button></>}>
    {(error || store.storageError) && <p className="file-symbol-error" role="alert">{error || store.storageError}</p>}
    {page === 'save' ? <><p>Enter name for the new data format.</p><Field label="Name"><TextInput value={name} maxLength={80} onChange={event => setName(event.target.value)}/></Field></> : page === 'delete' ? <p>Delete data format '{format.name}'?</p> : <>
      <fieldset><legend>Choose file</legend><div className="import-file-picker"><Field label="Data file"><TextInput readOnly value={filename}/></Field><Button disabled={busy} onClick={() => picker.current?.click()}>Browse</Button><input ref={picker} hidden aria-label="Choose data file" type="file" accept=".csv,.tsv,.txt" onChange={async event => {
        const file = event.target.files?.[0]; if (!file) return; const token = ++generation.current; setBusy(true); setError(''); setFilename(''); setText('');
        try { const content = await readImportFile(file); const detected = detectFormat(content); if (token !== generation.current) return; setText(content); setFilename(file.name); setFormat(detected); }
        catch (cause) { if (token === generation.current) setError(String(cause)); } finally { if (token === generation.current) setBusy(false); }
      }}/></div>
      <div className="import-grid"><Field label="Imported data timezone"><select aria-label="Imported data timezone" value={timezone} onChange={event => setTimezone(event.target.value)}>{timezones.map(([id, label]) => <option key={label} value={id}>{label}</option>)}</select></Field><Field label="Imported timeframe"><select aria-label="Imported timeframe" value={timeframe} onChange={event => setTimeframe(event.target.value)}><option value="auto">Recognize automatically</option><option>Intraday</option>{timeframes.map(value => <option key={value}>{value}</option>)}</select></Field></div></fieldset>
      <fieldset><legend>File format</legend><div className="import-format-picker"><Field label="Predefined file format"><select aria-label="Predefined file format" value={format.name} onChange={event => { const chosen = formats.find(row => row.name === event.target.value)!; setFormat(chosen.name === 'Custom' ? { ...format, name: 'Custom', predefined: false } : structuredClone(chosen)); }}>{formats.map(row => <option key={row.name}>{row.name}</option>)}</select></Field><Button disabled={format.predefined} onClick={() => saveFormat(false)}>Save</Button><Button onClick={() => saveFormat(true)}>Save as</Button><Button disabled={!store.formats.some(row => row.name === format.name)} onClick={() => { setPage('delete'); setError(''); }}>Delete</Button></div>
      <div className="import-grid three"><Field label="Skip rows"><TextInput type="number" min={0} max={1000} value={format.skipRows} onChange={event => change({ skipRows: event.target.valueAsNumber })}/></Field><Field label="Skip columns"><TextInput type="number" min={0} max={100} value={format.skipColumns} onChange={event => change({ skipColumns: event.target.valueAsNumber })}/></Field><Field label="Separator"><select aria-label="Separator" value={format.separator} onChange={event => change({ separator: event.target.value })}>{[[',', 'Comma'], [';', 'Semicolon'], ['\t', 'Tab'], ['|', 'Pipe'], [' ', 'Space']].map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></Field></div>
      <Field label="Date format"><TextInput aria-label="Date format" list="import-date-patterns" value={format.dateFormat} onChange={event => change({ dateFormat: event.target.value })}/><small>Example: {dateExample(format.dateFormat)}</small></Field><datalist id="import-date-patterns">{datePatterns.map(pattern => <option key={pattern}>{pattern}</option>)}</datalist>
      <div className="import-error-options"><strong>Data errors handling</strong><label><input type="radio" checked={!ignore} onChange={() => setIgnore(false)}/> Stop import</label><label><input type="radio" checked={ignore} onChange={() => setIgnore(true)}/> Ignore lines with errors</label></div>
      {preview.error && <p role="alert">{preview.error}</p>}
      <div className="import-preview"><table className="plain-table" aria-label="Data preview"><thead><tr>{Array.from({ length: width || 4 }, (_, index) => <th key={index}><select aria-label={`Column ${index + 1} type`} value={format.columns[index] ?? ''} onChange={event => change({ columns: Array.from({ length: width }, (_, i) => i === index ? event.target.value as ColumnType : format.columns[i] ?? '') })}>{columnTypes.map(type => <option value={type} key={type}>{type || 'Choose type...'}</option>)}</select></th>)}</tr></thead><tbody>{preview.rows.map((row, index) => <tr key={index}>{row.map((cell, i) => <td key={i}>{cell}</td>)}</tr>)}</tbody></table></div><small>{preview.count ? `Preview: first ${Math.min(50, preview.count)} of ${preview.count.toLocaleString()} rows` : 'Choose a file to preview its data.'}</small>
      </fieldset>
    </>}
  </Modal></div>;
}
