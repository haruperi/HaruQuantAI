import { Button, TextInput } from '../../../../components/ui';
import type { CryptoDefinition } from '../crypto';
import { CryptoModal } from '../add/addPopup';
import { today, type Preset } from '../../Dukascopy/dukascopyDownload';
import { useImportPopup } from './importPopupCtrl';

export function ImportPopup({ targets, onClose, onStarted }: { targets: CryptoDefinition[]; onClose: () => void; onStarted: () => void }) {
  const { store, minimum, from, setFrom, to, setTo, preset, setPreset, overwrite, setOverwrite, error, setError, choose, start } = useImportPopup(targets, onClose, onStarted);
  const presetButton = (value: Preset, label: string) => <Button aria-pressed={preset === value} className={preset === value ? 'primary' : ''} onClick={() => choose(value)}>{label}</Button>;
  return <CryptoModal title={`Download crypto data for ${targets.length > 1 ? 'multiple' : `'${targets[0].symbol}'`}`} onClose={onClose} footer={<><Button onClick={onClose}>Close</Button><Button className="primary" onClick={start}>Start download</Button></>}>
    {(error || store.storageError) && <p role="alert" className="crypto-error">{error || store.storageError}</p>}
    <fieldset><legend>Choose data range to download</legend><div className="crypto-date-row"><label>From <TextInput aria-label="From" type="date" min={minimum} max={today()} value={from} onChange={event => { setFrom(event.target.value); setPreset('custom'); setError(''); }}/></label>{presetButton('sinceLast','Since last date')}{presetButton('sixMonths','Last 6 months')}{presetButton('year','Last year')}</div><div className="crypto-date-row"><label>To <TextInput aria-label="To" type="date" min={minimum} max={today()} value={to} onChange={event => { setTo(event.target.value); setPreset('custom'); setError(''); }}/></label>{presetButton('fiveYears','Last 5 years')}{presetButton('tenYears','Last 10 years')}{presetButton('allTime','All time')}</div></fieldset>
    <fieldset><legend>Redownload options</legend><div className="crypto-redownload"><label><input type="radio" name="crypto-overwrite" checked={!overwrite} onChange={() => setOverwrite(false)}/> Add only missing data</label><label><input type="radio" name="crypto-overwrite" checked={overwrite} onChange={() => setOverwrite(true)}/> Overwrite existing data</label></div></fieldset>
    <p className="crypto-mock-note">This download is simulated. It stores date coverage metadata without contacting the exchange or creating market bars.</p>
  </CryptoModal>;
}
