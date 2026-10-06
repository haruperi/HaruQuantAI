import type { ReactNode } from 'react';
import { Button, Modal, TextInput } from '../../../../components/ui';
import type { CryptoExchangeId } from '../crypto';
import { useAddPopup } from './addPopupCtrl';
import '../style.css';

export function CryptoModal({ title, onClose, children, footer, wide = false }: { title: string; onClose: () => void; children: ReactNode; footer: ReactNode; wide?: boolean }) {
  return <div className={`crypto-flow ${wide ? 'crypto-wide' : ''}`} onKeyDown={event => {
    if (event.key !== 'Tab') return;
    const controls = Array.from(event.currentTarget.querySelectorAll<HTMLElement>('button:not(:disabled),input:not(:disabled),select:not(:disabled),a[href]'));
    if (event.shiftKey && document.activeElement === controls[0]) { event.preventDefault(); controls.at(-1)?.focus(); }
    else if (!event.shiftKey && document.activeElement === controls.at(-1)) { event.preventDefault(); controls[0]?.focus(); }
  }}><Modal title={title} width={wide ? 900 : 720} onClose={onClose} footer={footer}>{children}</Modal></div>;
}

export function AddPopup({ exchangeId, onClose, onStarted }: { exchangeId: CryptoExchangeId; onClose: () => void; onStarted: () => void }) {
  const { exchange, store, query, setQuery, selected, setSelected, timeframe, setTimeframe, postfix, setPostfix, agreed, setAgreed, error, setError, allCheck, rows, all, save } = useAddPopup(exchangeId, onClose, onStarted);
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
