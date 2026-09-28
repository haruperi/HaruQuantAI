import { useMemo, useState } from 'react';
import { Button, Checkbox, Field, Modal, Select, TextInput } from '../../../components/ui';
import { builtInCsvFormats, csvArtifacts, csvTokens, exportPreset, exportRange, exportSessions, exportTimezones, type CsvFormat, type ExportTarget } from './dataExport';
import { useDataExports } from './dataExportStore';
import type { Preset } from './presentation';
import './dataExport.css';

const presets: [Preset, string][] = [['sinceLast', 'Since last date'], ['sixMonths', 'Last 6 months'], ['year', 'Last year'], ['fiveYears', 'Last 5 years'], ['tenYears', 'Last 10 years'], ['allTime', 'All time']];

export function CsvExportDialog({ targets, externalActive, onClose, onStarted }: { targets: ExportTarget[]; externalActive: boolean; onClose: () => void; onStarted: () => void }) {
  const store = useDataExports();
  const range = useMemo(() => exportRange(targets), [targets]);
  const available = [...builtInCsvFormats, ...store.formats];
  const initial = available.find(item => item.name === store.settings.csvFormat) ?? available.find(item => item.name.includes(targets.some(row => row.timeframe.toUpperCase().includes('TICK')) ? 'tick' : 'bar')) ?? available[0];
  const [from, setFrom] = useState(range.from); const [to, setTo] = useState(range.to);
  const [preset, setPreset] = useState<Preset>('allTime');
  const [timeframe, setTimeframe] = useState(targets.some(row => row.timeframe.toUpperCase().includes('TICK')) ? 'Tick' : 'M1');
  const [session, setSession] = useState(String(store.settings.csvSession ?? 'No Session'));
  const [timezone, setTimezone] = useState(String(store.settings.csvTimezone ?? 'original'));
  const [formatName, setFormatName] = useState(initial.name); const [header, setHeader] = useState(initial.header); const [format, setFormat] = useState(initial.format);
  const [includeHeader, setIncludeHeader] = useState(Boolean(store.settings.csvIncludeHeader ?? true));
  const [prefix, setPrefix] = useState(String(store.settings.csvPrefix ?? new Date().toISOString().slice(0, 10)));
  const [newFormatOpen, setNewFormatOpen] = useState(false); const [deleteOpen, setDeleteOpen] = useState(false); const [newName, setNewName] = useState('');
  const [error, setError] = useState('');
  const selectedFormat = available.find(item => item.name === formatName);
  const suffix = `${targets.length === 1 ? targets[0].symbol : '[symbol]'}-${timeframe}-${session.replace(/\s+/g, '_')}.csv`;
  const title = targets.length === 1 ? `'${targets[0].symbol}'` : `${targets.length} selected records`;

  function selectFormat(name: string): void { const next = available.find(item => item.name === name); if (!next) return; setFormatName(name); setHeader(next.header); setFormat(next.format); setError(''); }
  function edit(setter: (value: string) => void, value: string): void { setter(value); setFormatName('Custom'); setError(''); }
  function choose(value: Preset): void { const next = exportPreset(value, range, from, to); setFrom(next.from); setTo(next.to); setPreset(value); setError(''); }
  function saveAs(): void {
    try { store.saveFormat({ name: newName, predefined: false, header, format }); setFormatName(newName.trim()); setNewName(''); setNewFormatOpen(false); setError(''); }
    catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to save format.'); }
  }
  function start(): void {
    try {
      const artifacts = csvArtifacts({ targets, from, to, timeframe, session, timezone, prefix, includeHeader, header, format });
      store.start('csv', 'CSV mock export', targets.map(row => row.id), artifacts,
        { csvFormat: formatName, csvSession: session, csvTimezone: timezone, csvIncludeHeader: includeHeader, csvPrefix: prefix }, externalActive);
      onStarted(); onClose();
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to start CSV export.'); }
  }
  const append = (kind: 'header' | 'format', token: string) => edit(kind === 'header' ? setHeader : setFormat, (kind === 'header' ? header : format) + token);
  return <div className="data-export-flow"><Modal title={`Export data for ${title}`} width={790} onClose={onClose} footer={<><Button onClick={onClose}>Close</Button><Button className="primary" onClick={start}>Export</Button></>}>
    {(error || store.storageError) && <p className="export-error" role="alert">{error || store.storageError}</p>}
    <fieldset><legend>Choose data range to export</legend><div className="export-date-grid"><label>From <TextInput aria-label="CSV date from" type="date" min={range.from} max={to} value={from} onChange={event => { setFrom(event.target.value); setPreset('custom'); }}/></label>{presets.slice(0, 3).map(([id, label]) => <Button key={id} aria-pressed={preset === id} className={preset === id ? 'primary' : ''} onClick={() => choose(id)}>{label}</Button>)}<label>To <TextInput aria-label="CSV date to" type="date" min={from} max={range.to} value={to} onChange={event => { setTo(event.target.value); setPreset('custom'); }}/></label>{presets.slice(3).map(([id, label]) => <Button key={id} aria-pressed={preset === id} className={preset === id ? 'primary' : ''} onClick={() => choose(id)}>{label}</Button>)}</div></fieldset>
    <fieldset><legend>Select timeframe, session and target timezone</legend><div className="export-grid three"><Field label="Timeframe"><Select value={timeframe} onChange={setTimeframe}>{targets.some(row => row.timeframe.toUpperCase().includes('TICK')) && <option>Tick</option>}{['M1','M5','M15','M30','H1','H4','D1'].map(item => <option key={item}>{item}</option>)}</Select></Field><Field label="Session"><Select value={session} onChange={setSession}>{exportSessions.map(item => <option key={item}>{item}</option>)}</Select></Field><Field label="Target timezone" hint="Choose Original to keep all timestamps unchanged."><Select value={timezone} onChange={setTimezone}>{exportTimezones.map(([id, label]) => <option value={id} key={id}>{label}</option>)}</Select></Field></div></fieldset>
    <fieldset><legend>File format</legend><div className="export-format-row"><Field label="Predefined / saved format"><Select value={formatName} onChange={selectFormat}><option value="Custom">Custom</option>{available.map(item => <option key={item.name}>{item.name}</option>)}</Select></Field><Button disabled={selectedFormat?.predefined || formatName === 'Custom'} onClick={() => { try { store.saveFormat({ name: formatName, predefined: false, header, format }, true); } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to save format.'); } }}>Save</Button><Button onClick={() => { setNewName(formatName === 'Custom' ? '' : `${formatName} copy`); setNewFormatOpen(true); }}>Save as</Button><Button disabled={selectedFormat?.predefined || formatName === 'Custom'} onClick={() => setDeleteOpen(true)}>Delete</Button></div>
      <div className="export-template-row"><Checkbox label="Include header" checked={includeHeader} onChange={setIncludeHeader}/><TextInput aria-label="CSV header" disabled={!includeHeader} value={header} onChange={event => edit(setHeader, event.target.value)}/><Select value="" onChange={value => { if (value) append('header', value); }}><option value="">Insert token…</option>{csvTokens.map(token => <option value={token} key={token}>{token === '\t' ? 'Tab' : token}</option>)}</Select></div>
      <div className="export-template-row"><span>Format</span><TextInput aria-label="CSV row format" value={format} onChange={event => edit(setFormat, event.target.value)}/><Select value="" onChange={value => { if (value) append('format', value); }}><option value="">Insert token…</option>{csvTokens.map(token => <option value={token} key={token}>{token === '\t' ? 'Tab' : token}</option>)}</Select></div>
    </fieldset>
    <fieldset><legend>Select target</legend><div className="export-target-grid"><Field label="Directory"><TextInput value="Browser downloads" readOnly/></Field><Button disabled title="Browser downloads are controlled by browser settings">Browse</Button><Field label="File prefix"><TextInput aria-label="CSV file prefix" value={prefix} onChange={event => setPrefix(event.target.value)}/></Field><span className="export-suffix">{suffix}</span></div><p className="export-mock-note">Offline mock export. Up to 180 deterministic sample rows are generated per selected dataset.</p></fieldset>
  </Modal>
  {newFormatOpen && <Modal title="New file format" width={470} onClose={() => setNewFormatOpen(false)} footer={<><Button onClick={() => setNewFormatOpen(false)}>Close</Button><Button className="primary" onClick={saveAs}>Save</Button></>}>{error && <p className="export-error" role="alert">{error}</p>}<p>Enter the name of the new file format</p><Field label="Name"><TextInput aria-label="New CSV format name" autoFocus value={newName} maxLength={80} onChange={event => { setNewName(event.target.value); setError(''); }}/></Field></Modal>}
  {deleteOpen && <Modal title="Delete file format" width={470} onClose={() => setDeleteOpen(false)} footer={<><Button onClick={() => setDeleteOpen(false)}>Cancel</Button><Button className="danger" onClick={() => { store.deleteFormat(formatName); selectFormat(builtInCsvFormats[0].name); setDeleteOpen(false); }}>Delete</Button></>}><p>Delete the saved format <strong>{formatName}</strong>?</p></Modal>}
  </div>;
}
