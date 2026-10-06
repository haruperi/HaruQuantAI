import type { ReactNode } from 'react';
import { Button, Modal, TextInput } from '../../../../components/ui';
import { useAddPopup } from './addPopupCtrl';
import { SelectInstrumentsPopup } from './selectInstrumentsPopup';
import { DarwinexConsent } from '../disclaimer/module';
import '../style.css';
import './styles.css';

export function DarwinexModal({ title, onClose, children, footer, wide = false }: { title: string; onClose: () => void; children: ReactNode; footer: ReactNode; wide?: boolean }) {
  return <div className={`darwinex-flow ${wide ? 'darwinex-wide' : ''}`} onKeyDown={event => {
    if (event.key !== 'Tab') return;
    const controls = Array.from(event.currentTarget.querySelectorAll<HTMLElement>('button:not(:disabled),input:not(:disabled):not([type=file]),select:not(:disabled),a[href]'));
    if (event.shiftKey && document.activeElement === controls[0]) { event.preventDefault(); controls.at(-1)?.focus(); }
    else if (!event.shiftKey && document.activeElement === controls.at(-1)) { event.preventDefault(); controls[0]?.focus(); }
  }}><Modal title={title} width={wide ? 900 : 720} onClose={onClose} footer={footer}>{children}</Modal></div>;
}
export function AddPopup({ onClose, onStarted }: { onClose: () => void; onStarted: () => void }) {
  const { data, store, query, setQuery, selected, setSelected, brokerId, setBroker, postfix, setPostfix, agreed, setAgreed, error, setError, notice, setNotice, mapping, mappings, setMappings, sort, setSort, descending, setDescending, warned, broker, rows, close, save, mass } = useAddPopup(onClose, onStarted);
  return <DarwinexModal key={mapping ? 'mapping' : 'add'} wide title={mapping ? 'Add Darwinex data - identify instruments' : 'Add Darwinex data'} onClose={close} footer={<>
    {!mapping && <DarwinexConsent agreed={agreed} setAgreed={setAgreed}/> }
    <Button onClick={close}>{mapping ? '< Back' : 'Close'}</Button><Button className="primary" onClick={save}>Save</Button>
  </>}>
    {(error || data.storageError || store.storageError) && <p role="alert" className="darwinex-error">{error || data.storageError || store.storageError}</p>}
    {mapping ? <SelectInstrumentsPopup broker={broker} selected={selected} mappings={mappings} setMappings={setMappings} mass={mass}/> : <fieldset className="darwinex-catalogue"><legend>Choose from available data</legend>
    <TextInput aria-label="Filter items" placeholder="Filter items" value={query} onChange={event => { setQuery(event.target.value); setSelected([]); }}/>
    <div className="darwinex-grid"><table className="plain-table" aria-label="Available Darwinex data"><thead><tr><th><input type="checkbox" aria-label="Select all Darwinex symbols" checked={rows.length > 0 && rows.every(row => selected.includes(row.symbol))} disabled={!rows.length} onChange={() => setSelected(rows.every(row => selected.includes(row.symbol)) ? [] : rows.map(row => row.symbol))}/></th>{(['symbol','dateFrom'] as const).map(key => <th key={key} aria-sort={sort === key ? descending ? 'descending' : 'ascending' : 'none'}><button onClick={() => { setDescending(sort === key && !descending); setSort(key); }}>{key === 'symbol' ? 'Symbol' : 'Available data range'}</button></th>)}</tr></thead><tbody>{rows.map(row => <tr key={row.symbol} className={selected.includes(row.symbol) ? 'selected' : ''}><td><input type="checkbox" aria-label={`Select symbol ${row.symbol}`} checked={selected.includes(row.symbol)} onChange={() => setSelected(current => current.includes(row.symbol) ? current.filter(item => item !== row.symbol) : [...current,row.symbol])}/></td><td>{row.symbol}</td><td>from {row.dateFrom.replaceAll('-','.')}</td></tr>)}{!rows.length && <tr><td colSpan={3}>No Darwinex symbols available.</td></tr>}</tbody></table></div>
    <div className="darwinex-details"><label>Broker profile * <select aria-label="Broker profile" value={brokerId} onChange={event => { const id = event.target.value; setBroker(id); setPostfix(data.brokers.find(row => row.id === id)?.postfix ?? ''); if (id !== '-1' && !warned.current) { warned.current = true; setNotice("You have selected a non-default broker. Data will be automatically adjusted to the broker's time zone during download."); } }}><option value="-1">Default</option>{data.brokers.filter(row => row.mtUse).map(row => <option key={row.id} value={row.id}>{row.name}</option>)}</select></label><label>Data postfix <TextInput aria-label="Data postfix" maxLength={64} value={postfix} onChange={event => setPostfix(event.target.value)}/><small>This postfix will be optionally added to the data names created</small></label></div>{notice && <p role="status">{notice}</p>}
    </fieldset>}
  </DarwinexModal>;
}
