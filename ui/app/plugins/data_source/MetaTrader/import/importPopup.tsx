import type { InputHTMLAttributes } from 'react';
import { Button, Modal, TextInput } from '../../../../components/ui';
import { today, type Preset } from '../../Dukascopy/dukascopyDownload';
import { useMt5ApiImport } from './DataSourceMt5ApiImportCtrl';
import '../styles.css';

export function ImportPopup({ onClose, onStarted }: { onClose: () => void; onStarted: () => void }) {
  const { store, notify, picker, folder, fetched, loading, query, setQuery, category, setCategory, selected, setSelected, from, setFrom, to, setTo, preset, setPreset, broker, setBroker, postfix, setPostfix, error, setError, brokers, visible, categories, allVisible, grouped, fetchSymbols, choose, start, chooseFolder } = useMt5ApiImport(onClose, onStarted);
  const presetButton = (value: Preset, label: string) => <Button aria-pressed={preset === value} className={preset === value ? 'primary' : ''} onClick={() => choose(value)}>{label}</Button>;

  return <div className="mt5-flow" onKeyDown={event => {
    if (event.key !== 'Tab') return;
    const controls = Array.from(event.currentTarget.querySelectorAll<HTMLElement>('button:not(:disabled),input:not(:disabled):not([type=file]),select:not(:disabled),a[href]'));
    if (event.shiftKey && document.activeElement === controls[0]) { event.preventDefault(); controls.at(-1)?.focus(); }
    else if (!event.shiftKey && document.activeElement === controls.at(-1)) { event.preventDefault(); controls[0]?.focus(); }
  }}><Modal title="Import data from MT5" width={730} onClose={onClose} footer={<><Button onClick={onClose}>Close</Button><Button className="primary" disabled={loading} onClick={start}>Start import</Button></>}>
    {(error || store.storageError) && <p className="mt5-error" role="alert">{error || store.storageError}</p>}
    <fieldset className="mt5-main">
      <div className="mt5-folder-row"><label htmlFor="mt5-folder">MT5 install folder</label><TextInput id="mt5-folder" readOnly value={folder?.folder ?? store.folder}/><button className="mt5-link" onClick={() => picker.current?.click()}>Select</button>
        <input ref={picker} hidden type="file" aria-label="Select MT5 installation folder" {...({ webkitdirectory: '', directory: '' } as InputHTMLAttributes<HTMLInputElement>)} onChange={chooseFolder}/>
      </div>
      {!folder && store.folder && <small className="mt5-reselect">Select the folder again to fetch its available symbols.</small>}
      <div className="mt5-filter-row"><Button className="primary" disabled={loading} onClick={fetchSymbols}>{loading ? 'Fetching…' : 'Fetch symbols'}</Button><TextInput aria-label="Filter items" placeholder="Filter items" value={query} disabled={!fetched} onChange={event => { setQuery(event.target.value); setSelected([]); }}/><label>Show types <select aria-label="Show types" disabled={!fetched} value={category} onChange={event => { setCategory(event.target.value); setSelected([]); }}><option value="">All</option>{categories.map(path => <option key={path}>{path}</option>)}</select></label></div>

      <label className="mt5-range-label">Download range</label>
      <div className="mt5-date-row"><label>From <TextInput aria-label="From" type="date" max={to} value={from} onChange={event => { setFrom(event.target.value); setPreset('custom'); setError(''); }}/></label>{presetButton('sinceLast', 'Since last date')}{presetButton('sixMonths', 'Last 6 months')}{presetButton('year', 'Last year')}</div>
      <div className="mt5-date-row"><label>To <TextInput aria-label="To" type="date" min={from} max={today()} value={to} onChange={event => { setTo(event.target.value); setPreset('custom'); setError(''); }}/></label>{presetButton('fiveYears', 'Last 5 years')}{presetButton('tenYears', 'Last 10 years')}{presetButton('allTime', 'All time')}</div>

      <section className="mt5-disclaimer" aria-label="Data Availability Disclaimer"><p><strong>Data Availability Disclaimer</strong></p><p>MetaTrader 5 imports depend on the historical data provided by your broker. Some brokers only supply a limited history (e.g., a few months), which may result in incomplete imports.</p><p>To improve data coverage, go to Tools → Options → Charts, set “Max bars in chart” to a high value (e.g., 99,999,999), and restart MetaTrader 5.&nbsp;&nbsp;<button className="mt5-link" onClick={() => notify('MT5 import help is not configured for this HaruQuantAI workspace')}>More details</button></p></section>

      <div className="mt5-symbol-grid"><table className="plain-table" aria-label="MT5 symbols"><thead><tr><th><input type="checkbox" aria-label="Select all visible MT5 symbols" disabled={!visible.length} checked={allVisible} onChange={() => setSelected(current => allVisible ? current.filter(name => !visible.some(row => row.name === name)) : [...new Set([...current, ...visible.map(row => row.name)])])}/></th><th>Symbol</th><th>Name</th></tr></thead><tbody>
        {grouped.flatMap(group => [<tr className="mt5-category" key={`group:${group.path}`}><td><input type="checkbox" aria-label={`Select group ${group.path}`} checked={group.rows.every(row => selected.includes(row.name))} onChange={event => setSelected(current => event.target.checked ? [...new Set([...current, ...group.rows.map(row => row.name)])] : current.filter(name => !group.rows.some(row => row.name === name)))}/></td><td colSpan={2}>{group.path}</td></tr>, ...group.rows.map(row => <tr key={row.name} className={selected.includes(row.name) ? 'selected' : ''}><td><input type="checkbox" aria-label={`Select MT5 symbol ${row.name}`} checked={selected.includes(row.name)} onChange={() => setSelected(current => current.includes(row.name) ? current.filter(name => name !== row.name) : [...current, row.name])}/></td><td>{row.name}</td><td>{row.description}</td></tr>)])}
        {!visible.length && <tr><td colSpan={3}>{loading ? 'Loading symbols...' : 'No symbols available.'}</td></tr>}
      </tbody></table></div>

      <div className="mt5-details"><label>Broker profile * <select aria-label="Broker profile" value={broker} onChange={event => { const profile = brokers.find(item => item.id === event.target.value); setBroker(event.target.value); setPostfix(profile?.postfix ?? ''); setError(''); }}>{brokers.map(item => <option value={item.id} key={item.id}>{item.name}</option>)}</select></label><label>Data postfix <span><TextInput aria-label="Data postfix" maxLength={64} value={postfix} onChange={event => { setPostfix(event.target.value); setError(''); }}/><small>This postfix will be added to the data names</small></span></label></div>
      <p className="mt5-mock-note">Offline mock terminal discovery. File contents are not read and MetaTrader is not started.</p>
    </fieldset>
  </Modal></div>;
}
