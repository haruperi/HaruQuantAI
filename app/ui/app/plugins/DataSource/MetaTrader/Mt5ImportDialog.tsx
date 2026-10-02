import { useState } from 'react';
import { Button, Modal, TextInput } from '../../../components/ui';
import { filterMt5Symbols, groupMt5Symbols, mt5Definitions, mt5Preset } from './mt5Import';
import { useMt5Import } from './mt5ImportStore';
import { today, type Preset, type BrokerProfile } from './presentation';
import './mt5Import.css';

export interface Mt5ContextDocument {
  readonly existing: readonly string[];
  readonly active: boolean;
  readonly error: string;
  readonly brokers?: readonly BrokerProfile[];
}

function initialFrom(): string {
  const date = new Date(`${today()}T12:00:00Z`);
  date.setUTCFullYear(date.getUTCFullYear() - 1);
  return date.toISOString().slice(0, 10);
}

export function Mt5ImportDialog({
  contextDocument,
  onClose,
  onStarted,
}: {
  contextDocument?: Mt5ContextDocument;
  onClose: () => void;
  onStarted: () => void;
}) {
  const store = useMt5Import();
  const initialDate = initialFrom();
  const [folder, setFolder] = useState(store.folder);
  const [fetched, setFetched] = useState(false);
  const [loading, setLoading] = useState(false);
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState('');
  const [selected, setSelected] = useState<string[]>([]);
  const [from, setFrom] = useState(initialDate);
  const [to, setTo] = useState(today());
  const [preset, setPreset] = useState<Preset>('sinceLast');
  const [broker, setBroker] = useState('-1');
  const [postfix, setPostfix] = useState(store.postfix);
  const [error, setError] = useState('');

  const availableBrokers = (contextDocument?.brokers && contextDocument.brokers.length > 0)
    ? contextDocument.brokers
    : store.brokers;
  const brokers = [{ id: '-1', name: 'Default', postfix: '', timezone: 'UTC', mtUse: true, instruments: [] },
    ...availableBrokers];
  const visible = fetched ? filterMt5Symbols(query, category, store.symbols) : [];
  const categories = groupMt5Symbols(store.symbols);
  const allVisible = visible.length > 0 && visible.every(row => selected.includes(row.name));
  const grouped = groupMt5Symbols(visible);

  function clearResults(): void { setFetched(false); setLoading(false); setQuery(''); setCategory(''); setSelected([]); }
  async function fetchSymbols(): Promise<void> {
    setError(''); setLoading(true); setFetched(false); setSelected([]);
    try { await store.connect(folder); setFetched(true); }
    catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to connect to the terminal.'); }
    finally { setLoading(false); }
  }
  function choose(value: Preset): void {
    const range = value === 'sinceLast' ? { from: initialDate, to } : mt5Preset(value, from, to);
    setFrom(range.from); setTo(range.to); setPreset(value); setError('');
  }
  async function start(): Promise<void> {
    try {
      if (!fetched) throw new Error('Use global MT5 settings or enter a terminal executable path, then fetch symbols.');
      const profile = brokers.find(item => item.id === broker);
      if (!profile) throw new Error('Choose a valid broker profile.');
      const request = { folder, symbols: selected, dateFrom: from, dateTo: to, dateType: preset,
        broker: profile.id, brokerName: profile.name, timezone: profile.timezone, postfix };
      if (contextDocument?.error) throw new Error(contextDocument.error);
      const existing = contextDocument?.existing ? [...contextDocument.existing] : [];
      const active = contextDocument?.active ?? false;
      await store.start(request, mt5Definitions(request, existing, store.symbols), active);
      onStarted(); onClose();
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to start MT5 import.'); }
  }
  const presetButton = (value: Preset, label: string) => <Button aria-pressed={preset === value} className={preset === value ? 'primary' : ''} onClick={() => choose(value)}>{label}</Button>;

  return <div className="mt5-flow" onKeyDown={event => {
    if (event.key !== 'Tab') return;
    const controls = Array.from(event.currentTarget.querySelectorAll<HTMLElement>('button:not(:disabled),input:not(:disabled):not([type=file]),select:not(:disabled),a[href]'));
    if (event.shiftKey && document.activeElement === controls[0]) { event.preventDefault(); controls.at(-1)?.focus(); }
    else if (!event.shiftKey && document.activeElement === controls.at(-1)) { event.preventDefault(); controls[0]?.focus(); }
  }}><Modal title="Import data from MT5" width={730} onClose={onClose} footer={<><Button onClick={onClose}>Close</Button><Button className="primary" disabled={loading} onClick={start}>Start import</Button></>}>
    {(error || store.storageError) && <p className="mt5-error" role="alert">{error || store.storageError}</p>}
    <fieldset className="mt5-main">
      <div className="mt5-folder-row"><label htmlFor="mt5-folder">MT5 terminal</label><TextInput id="mt5-folder" placeholder="Use enabled global MT5 settings, or enter terminal64.exe path" value={folder} onChange={event => { setFolder(event.target.value); clearResults(); }}/><button className="mt5-link" onClick={() => { setFolder(''); clearResults(); }}>Use global settings</button></div>
      <div className="mt5-filter-row"><Button className="primary" disabled={loading} onClick={fetchSymbols}>{loading ? 'Fetching…' : 'Fetch symbols'}</Button><TextInput aria-label="Filter items" placeholder="Filter items" value={query} disabled={!fetched} onChange={event => { setQuery(event.target.value); setSelected([]); }}/><label><span>Show types</span><select aria-label="Show types" disabled={!fetched} value={category} onChange={event => { setCategory(event.target.value); setSelected([]); }}><option value="">All</option>{categories.map(group => <option value={group.key} key={group.key} title={group.label}>{group.label}</option>)}</select></label></div>

      <label className="mt5-range-label">Download range</label>
      <div className="mt5-date-row"><label>From <TextInput aria-label="From" type="date" max={to} value={from} onChange={event => { setFrom(event.target.value); setPreset('custom'); setError(''); }}/></label>{presetButton('sinceLast', 'Since last date')}{presetButton('sixMonths', 'Last 6 months')}{presetButton('year', 'Last year')}</div>
      <div className="mt5-date-row"><label>To <TextInput aria-label="To" type="date" min={from} max={today()} value={to} onChange={event => { setTo(event.target.value); setPreset('custom'); setError(''); }}/></label>{presetButton('fiveYears', 'Last 5 years')}{presetButton('tenYears', 'Last 10 years')}{presetButton('allTime', 'All time')}</div>

      <section className="mt5-disclaimer" aria-label="Data Availability Disclaimer"><p><strong>Data Availability Disclaimer</strong></p><p>MetaTrader 5 imports depend on the historical data provided by your broker. Some brokers only supply a limited history (e.g., a few months), which may result in incomplete imports.</p><p>To improve data coverage, go to Tools → Options → Charts, set “Max bars in chart” to a high value (e.g., 99,999,999), and restart MetaTrader 5.</p></section>

      <div className="mt5-symbol-grid"><table className="plain-table" aria-label="MT5 symbols"><thead><tr><th><input type="checkbox" aria-label="Select all visible MT5 symbols" disabled={!visible.length} checked={allVisible} onChange={() => setSelected(current => allVisible ? current.filter(name => !visible.some(row => row.name === name)) : [...new Set([...current, ...visible.map(row => row.name)])])}/></th><th>Symbol</th><th>Name</th></tr></thead><tbody>
        {grouped.flatMap(group => [<tr className="mt5-category" key={group.key}><td><input type="checkbox" aria-label={`Select group ${group.label}`} checked={group.rows.every(row => selected.includes(row.name))} onChange={event => setSelected(current => event.target.checked ? [...new Set([...current, ...group.rows.map(row => row.name)])] : current.filter(name => !group.rows.some(row => row.name === name)))}/></td><td colSpan={2}>{group.label}</td></tr>, ...group.rows.map(row => <tr key={row.name} className={selected.includes(row.name) ? 'selected' : ''}><td><input type="checkbox" aria-label={`Select MT5 symbol ${row.name}`} checked={selected.includes(row.name)} onChange={() => setSelected(current => current.includes(row.name) ? current.filter(name => name !== row.name) : [...current, row.name])}/></td><td>{row.name}</td><td>{row.description}</td></tr>)])}
        {!visible.length && <tr><td colSpan={3}>{loading ? 'Loading symbols...' : 'No symbols available.'}</td></tr>}
      </tbody></table></div>

      <div className="mt5-details"><label>Broker profile * <select aria-label="Broker profile" value={broker} onChange={event => { const profile = brokers.find(item => item.id === event.target.value); setBroker(event.target.value); setPostfix(profile?.postfix ?? ''); setError(''); }}>{brokers.map(item => <option value={item.id} key={item.id}>{item.name}</option>)}</select></label><label>Data postfix <span><TextInput aria-label="Data postfix" maxLength={64} value={postfix} onChange={event => { setPostfix(event.target.value); setError(''); }}/><small>This postfix will be added to the data names</small></span></label></div>
      <p className="mt5-mock-note">Symbols and history are read from your connected MetaTrader 5 terminal.</p>
    </fieldset>
  </Modal></div>;
}
