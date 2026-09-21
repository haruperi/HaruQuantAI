import { useState } from 'react';
import { Button, TextInput } from '../../../components/ui';
import { useAppStore } from '../../../app/store';
import { DarwinexModal, darwinexContext } from './DarwinexAddDialog';
import { darwinexStart, type DarwinexDefinition } from './darwinex';
import { useDarwinex } from './darwinexStore';
import { today, presetRange, type Preset } from '../Dukascopy/dukascopyDownload';
export function DarwinexDownloadDialog({ targets, onClose, onStarted }: { targets: DarwinexDefinition[]; onClose: () => void; onStarted: () => void }) {
  const full = useAppStore(state => state.settings.profile) === 'Full'; const notify = useAppStore(state => state.notify); const store = useDarwinex();
  const minimum = darwinexStart(targets[0]), last = targets[0].to || minimum;
  const [from, setFrom] = useState(last), [to, setTo] = useState(today()), [preset, setPreset] = useState<Preset>('sinceLast'), [overwrite, setOverwrite] = useState(false), [error, setError] = useState('');
  function choose(value: Preset) { const range = presetRange(value, last, minimum, from, to); setFrom(range.from); setTo(range.to); setPreset(value); setError(''); }
  function start() { try { store.download({ targets, dateFrom: from, dateTo: to, dateType: preset, overwrite }, useAppStore.getState().settings.profile === 'Full', darwinexContext().active); onStarted(); onClose(); } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to start download.'); } }
  const button = (value: Preset, label: string) => <Button aria-pressed={preset === value} className={preset === value ? 'primary' : ''} onClick={() => choose(value)}>{label}</Button>;
  return <DarwinexModal title={`Download Darwinex data for ${targets.length > 1 ? 'multiple' : `'${targets[0].symbol}'`}`} onClose={onClose} footer={<><Button onClick={onClose}>Close</Button>{full && <Button className="primary" onClick={start}>Start download</Button>}</>}>
    {(error || store.storageError) && <p role="alert" className="darwinex-error">{error || store.storageError}</p>}
    {full ? <><fieldset><legend>Choose data range to download</legend><div className="darwinex-date-row"><label>From <TextInput aria-label="From" type="date" min={minimum} max={today()} value={from} onChange={event => { setFrom(event.target.value); setPreset('custom'); setError(''); }}/></label>{button('sinceLast','Since last date')}{button('sixMonths','Last 6 months')}{button('year','Last year')}</div><div className="darwinex-date-row"><label>To <TextInput aria-label="To" type="date" min={minimum} max={today()} value={to} onChange={event => { setTo(event.target.value); setPreset('custom'); setError(''); }}/></label>{button('fiveYears','Last 5 years')}{button('tenYears','Last 10 years')}{button('allTime','All time')}</div></fieldset><fieldset><legend>Redownload options</legend><div className="darwinex-mass"><label><input type="radio" name="darwinex-overwrite" checked={!overwrite} onChange={() => setOverwrite(false)}/> Add only missing data</label><label><input type="radio" name="darwinex-overwrite" checked={overwrite} onChange={() => setOverwrite(true)}/> Overwrite existing data</label></div></fieldset></> : <div className="darwinex-restricted"><p>Darwinex CDN download is available only for users of full license.</p><Button onClick={() => notify('License upgrades are not configured for this HaruQuantAI workspace')}>Upgrade To Pro Version</Button></div>}
  </DarwinexModal>;
}
