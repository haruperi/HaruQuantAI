import { useState } from 'react';
import { Button, TextInput } from '../../../components/ui';
import { cryptoStart, type CryptoDefinition } from './crypto';
import { useCrypto } from './cryptoStore';
import { CryptoModal, cryptoContext } from './CryptoAddDialog';
import { presetRange, today, type Preset } from '../Dukascopy/dukascopyDownload';

export function CryptoDownloadDialog({ targets, onClose, onStarted }: { targets: CryptoDefinition[]; onClose: () => void; onStarted: () => void }) {
  const store = useCrypto(), minimum = cryptoStart(targets[0]), last = targets[0].to || minimum;
  const [from, setFrom] = useState(last), [to, setTo] = useState(today()), [preset, setPreset] = useState<Preset>('sinceLast'), [overwrite, setOverwrite] = useState(false), [error, setError] = useState('');
  function choose(value: Preset) { const range = presetRange(value, last, minimum, from, to); setFrom(range.from); setTo(range.to); setPreset(value); setError(''); }
  function start() { try { store.startDownload({ targets, dateFrom: from, dateTo: to, dateType: preset, overwrite }, cryptoContext().active); onStarted(); onClose(); } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to start Crypto download.'); } }
  const presetButton = (value: Preset, label: string) => <Button aria-pressed={preset === value} className={preset === value ? 'primary' : ''} onClick={() => choose(value)}>{label}</Button>;
  return <CryptoModal title={`Download crypto data for ${targets.length > 1 ? 'multiple' : `'${targets[0].symbol}'`}`} onClose={onClose} footer={<><Button onClick={onClose}>Close</Button><Button className="primary" onClick={start}>Start download</Button></>}>
    {(error || store.storageError) && <p role="alert" className="crypto-error">{error || store.storageError}</p>}
    <fieldset><legend>Choose data range to download</legend><div className="crypto-date-row"><label>From <TextInput aria-label="From" type="date" min={minimum} max={today()} value={from} onChange={event => { setFrom(event.target.value); setPreset('custom'); setError(''); }}/></label>{presetButton('sinceLast','Since last date')}{presetButton('sixMonths','Last 6 months')}{presetButton('year','Last year')}</div><div className="crypto-date-row"><label>To <TextInput aria-label="To" type="date" min={minimum} max={today()} value={to} onChange={event => { setTo(event.target.value); setPreset('custom'); setError(''); }}/></label>{presetButton('fiveYears','Last 5 years')}{presetButton('tenYears','Last 10 years')}{presetButton('allTime','All time')}</div></fieldset>
    <fieldset><legend>Redownload options</legend><div className="crypto-redownload"><label><input type="radio" name="crypto-overwrite" checked={!overwrite} onChange={() => setOverwrite(false)}/> Add only missing data</label><label><input type="radio" name="crypto-overwrite" checked={overwrite} onChange={() => setOverwrite(true)}/> Overwrite existing data</label></div></fieldset>
    <p className="crypto-mock-note">This download is simulated. It stores date coverage metadata without contacting the exchange or creating market bars.</p>
  </CryptoModal>;
}
