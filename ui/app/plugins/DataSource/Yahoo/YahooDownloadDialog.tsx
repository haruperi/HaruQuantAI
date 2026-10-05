import { useState } from 'react';
import { Button, TextInput } from '../../../components/ui';
import { presetRange, today, type Preset } from './presentation';
import { yahooStart, type YahooDefinition } from './yahoo';
import { useYahoo } from './yahooStore';
import { YahooModal, yahooContext, type YahooContextDocument } from './YahooAddDialog';

export function YahooDownloadDialog({ contextDocument, targets, onClose, onStarted }: { contextDocument: YahooContextDocument; targets: YahooDefinition[]; onClose: () => void; onStarted: () => void }) {
  const store = useYahoo(), minimum = targets.map(yahooStart).sort()[0], now = today();
  const initial = presetRange('sixMonths', targets[0].to || minimum, minimum, minimum, now);
  const [from, setFrom] = useState(initial.from), [to, setTo] = useState(initial.to), [preset, setPreset] = useState<Preset>('custom'), [overwrite, setOverwrite] = useState(false), [error, setError] = useState('');
  function choose(value: Preset) { const range = presetRange(value, targets[0].to || minimum, minimum, from, to); setFrom(range.from); setTo(range.to); setPreset(value); setError(''); }
  async function start() { try { await store.startDownload({ targets, dateFrom: from, dateTo: to, dateType: preset, overwrite }, yahooContext(contextDocument).active); onStarted(); onClose(); } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to start Yahoo download.'); } }
  const presetButton = (value: Preset, label: string) => <Button aria-pressed={preset === value} className={preset === value ? 'primary' : ''} onClick={() => choose(value)}>{label}</Button>;
  return <YahooModal title={`Download Yahoo data for ${targets.length > 1 ? 'multiple' : `'${targets[0].symbol}'`}`} onClose={onClose} footer={<><Button onClick={onClose}>Close</Button><Button className="primary" onClick={start}>Start download</Button></>}>
    {(error || store.storageError) && <p role="alert" className="yahoo-error">{error || store.storageError}</p>}
    <fieldset><legend>Choose data range to download</legend><div className="yahoo-date-row"><label>From <TextInput aria-label="From" type="date" min={minimum} max={now} value={from} onChange={event => { setFrom(event.target.value); setPreset('custom'); setError(''); }}/></label>{presetButton('sinceLast','Since last date')}{presetButton('sixMonths','Last 6 months')}{presetButton('year','Last year')}</div><div className="yahoo-date-row"><label>To <TextInput aria-label="To" type="date" min={minimum} max={now} value={to} onChange={event => { setTo(event.target.value); setPreset('custom'); setError(''); }}/></label>{presetButton('fiveYears','Last 5 years')}{presetButton('tenYears','Last 10 years')}{presetButton('allTime','All time')}</div></fieldset>
    <fieldset><legend>Redownload options</legend><div className="yahoo-redownload"><label><input type="radio" name="yahoo-overwrite" checked={!overwrite} onChange={() => setOverwrite(false)}/> Add only missing data</label><label><input type="radio" name="yahoo-overwrite" checked={overwrite} onChange={() => setOverwrite(true)}/> Overwrite existing data</label></div></fieldset>
    <p className="yahoo-mock-note">Downloads are saved by the backend. Progress reflects the running acquisition job.</p>
  </YahooModal>;
}
