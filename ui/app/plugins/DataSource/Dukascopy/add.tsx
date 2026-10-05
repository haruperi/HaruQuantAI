/** Register Dukascopy dataset definitions directly from the symbol picker. */
import { useEffect, useMemo, useRef, useState } from 'react';
import { categories, filterCatalogue } from './dukascopy';
import type { BrokerProfile } from './presentation';
import './dukascopy.css';

export interface DukascopyContextDocument {
  readonly existing: readonly string[];
  readonly active: boolean;
  readonly error: string;
  readonly brokers?: readonly BrokerProfile[];
  readonly brokerCatalogStatus?: 'available' | 'unavailable';
}

const disclaimer = 'I confirm that I understand the following: Data are provided for free by Dukascopy. HaruQuantAI Data Manager is only a tool to download the data directly to the program. HaruQuantAI is not responsible for quality or availability of the data.';

export function DukascopyAddDialog({
  open,
  contextDocument,
  onClose,
  onAddData,
  onComplete,
  available = false,
}: {
  open: boolean;
  contextDocument?: DukascopyContextDocument;
  onClose: () => void;
  onAddData?: (request: { symbols: string[]; dataType: 'TICK' | 'M1'; broker: string; postfix: string; instruments: string[] }) => Promise<void>;
  onComplete: (message: string) => void;
  available?: boolean;
}) {
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState('');
  const [selected, setSelected] = useState<string[]>([]);
  const [dataType, setDataType] = useState<'TICK' | 'M1'>('TICK');
  const [broker, setBroker] = useState('-1');
  const [postfix, setPostfix] = useState('');
  const [confirmed, setConfirmed] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [warning, setWarning] = useState(false);
  const brokers = contextDocument?.brokers ?? [];
  const storageError = contextDocument?.error ?? '';
  const rows = useMemo(() => filterCatalogue(query, category), [query, category]);
  const groups = useMemo(() => Array.from(new Set(rows.map(row => row.fullCategory))).map(name => ({ name, rows: rows.filter(row => row.fullCategory === name) })), [rows]);
  const root = useRef<HTMLDivElement>(null);
  const headerCheck = useRef<HTMLInputElement>(null);
  const all = rows.length > 0 && rows.every(row => selected.includes(row.symbol));
  useEffect(() => { if (headerCheck.current) headerCheck.current.indeterminate = !all && selected.length > 0; }, [all, selected]);
  useEffect(() => {
    if (!open) return;
    setSelected([]); setConfirmed(false); setError(''); setWarning(false);
    setBroker('-1'); setPostfix('');
    const previous = document.activeElement as HTMLElement | null;
    root.current?.querySelector<HTMLButtonElement>('button')?.focus();
    return () => previous?.focus();
  }, [open]);
  useEffect(() => {
    if (broker !== '-1' && !brokers.some(item => item.id === broker)) {
      setBroker('-1'); setPostfix('');
    }
  }, [broker, brokers]);
  const changeFilter = (text: string, type: string) => { setQuery(text); setCategory(type); setSelected([]); };
  const toggle = (symbols: string[]) => setSelected(current => symbols.every(symbol => current.includes(symbol)) ? current.filter(symbol => !symbols.includes(symbol)) : [...new Set([...current, ...symbols])]);
  const save = async () => {
    if (saving || !available) return;
    setError('');
    if (!selected.length) { setError('No symbols selected'); return; }
    if (!confirmed) { setError(disclaimer); return; }
    const symbols = selected;
    setSaving(true);
    try {
      if (onAddData) {
        await onAddData({ symbols, dataType, broker, postfix, instruments: [] });
      }
      onComplete(`${symbols.length} Dukascopy dataset definition${symbols.length === 1 ? '' : 's'} added`);
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to add symbols'); } finally { setSaving(false); }
  };
  if (!open) return null;
  return <div className="dukas-overlay"><div ref={root} className="dukas-dialog" role="dialog" aria-modal="true" aria-labelledby="dukas-title" onKeyDown={event => {
    if (event.key === 'Escape') { event.stopPropagation(); onClose(); }
    if (event.key === 'Tab') {
      const controls = Array.from(root.current?.querySelectorAll<HTMLElement>('button:not(:disabled), input:not(:disabled), select:not(:disabled)') ?? []);
      const first = controls[0]; const last = controls[controls.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
      if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
    }
  }}>
    <header><h2 id="dukas-title">Add Dukascopy data</h2><button aria-label="Close" onClick={onClose}>×</button></header>
    <div className="dukas-body">
      <section className="dukas-panel">
        <strong>Choose from available data</strong>
        <div className="dukas-filters"><input aria-label="Filter available symbols" placeholder="Filter items" value={query} onChange={event => changeFilter(event.target.value, category)}/><label>Show types <select value={category} onChange={event => changeFilter(query, event.target.value)}>{categories.map(item => <option key={item.value} value={item.value}>{item.name}</option>)}</select></label></div>
        <div className="dukas-grid"><table aria-label="Available Dukascopy symbols"><colgroup><col style={{ width: 24 }}/><col style={{ width: 150 }}/><col style={{ width: 200 }}/><col style={{ width: 200 }}/><col style={{ width: 200 }}/></colgroup><thead><tr><th><input ref={headerCheck} type="checkbox" aria-label="Select all available symbols" checked={all} disabled={!rows.length} onChange={() => toggle(rows.map(row => row.symbol))}/></th><th>Symbol</th><th>Name</th><th>Available M1 data range</th><th>Available Tick data range</th></tr></thead>
          <tbody>{groups.map(group => <Group key={group.name} group={group} selected={selected} toggle={toggle}/>)}{!rows.length && <tr><td colSpan={5}>No Dukascopy symbols available.</td></tr>}</tbody></table></div>
        <div className="dukas-options"><strong>Data type</strong><label><input type="radio" name="dukas-type" checked={dataType === 'TICK'} onChange={() => setDataType('TICK')}/> Tick data</label><label><input type="radio" name="dukas-type" checked={dataType === 'M1'} onChange={() => setDataType('M1')}/> M1 data</label></div>
        <div className="dukas-settings"><label><strong>Broker profile *</strong><select aria-label="Broker profile *" value={broker} onChange={event => { const id = event.target.value; setBroker(id); setPostfix(brokers.find(item => item.id === id)?.postfix ?? ''); setWarning(id !== '-1'); }}><option value="-1">Default</option>{brokers.filter(item => item.mtUse).map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label><label><strong>Data postfix</strong><span><input aria-label="Data postfix" value={postfix} onChange={event => setPostfix(event.target.value)}/><small>This postfix will be optionally added to the data names created</small></span></label></div>
        {contextDocument?.brokerCatalogStatus === 'unavailable' && <p role="status">Broker profiles are unavailable from the database.</p>}
        {warning && <p className="dukas-warning" role="status">You have selected a non-default broker. Stored data remain UTC.</p>}
      </section>
    </div>
    <footer><label className="dukas-consent"><input role="switch" type="checkbox" checked={confirmed} onChange={event => setConfirmed(event.target.checked)}/><span>{disclaimer}</span></label>
      {(error || storageError) && <p className="dukas-error" role="alert">{error || storageError}</p>}
      {!available && <p role="status">Dataset storage is unavailable. Reconnect to the host or check the dataset catalog.</p>}
      <div className="dukas-actions"><button className="dukas-link sq-button" onClick={onClose}>Close</button><button className="dukas-save sq-button primary" onClick={() => { void save(); }} disabled={!available || !selected.length || !confirmed || saving}>{saving ? 'Saving...' : 'Save'}</button></div>
    </footer>
  </div></div>;
}

function Group({ group, selected, toggle }: { group: { name: string; rows: ReturnType<typeof filterCatalogue> }; selected: string[]; toggle: (symbols: string[]) => void }) {
  const ref = useRef<HTMLInputElement>(null);
  const count = group.rows.filter(row => selected.includes(row.symbol)).length;
  useEffect(() => { if (ref.current) ref.current.indeterminate = count > 0 && count < group.rows.length; }, [count, group.rows.length]);
  return <><tr className="dukas-group"><td><input ref={ref} type="checkbox" aria-label={`Select ${group.name}`} checked={count === group.rows.length} onChange={() => toggle(group.rows.map(row => row.symbol))}/></td><td colSpan={4}>{group.name}</td></tr>{group.rows.map(row => <tr key={row.symbol} className={selected.includes(row.symbol) ? 'dukas-selected' : ''}><td><input type="checkbox" aria-label={`Select symbol ${row.symbol}`} checked={selected.includes(row.symbol)} onChange={() => toggle([row.symbol])}/></td><td>{row.symbol}</td><td>{row.name}</td><td>from {row.dateFromM1.replaceAll('-', '.')}</td><td>from {row.dateFrom.replaceAll('-', '.')}</td></tr>)}</>;
}

export default DukascopyAddDialog;
