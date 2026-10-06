import { Button, TextInput } from '../../../../components/ui';
import type { Preset } from '../../Dukascopy/dukascopyDownload';
import { YahooModal } from '../add/addPopup';
import { useYahooDownload, type YahooDownloadProps } from './downloadPopupCtrl';
export function YahooDownloadDialog(props: YahooDownloadProps) {
  const { targets, onClose } = props;
  const { store, minimum, now, from, setFrom, to, setTo, preset, setPreset, overwrite, setOverwrite, error, setError, choose, start } = useYahooDownload(props);
  const presetButton = (value: Preset, label: string) => <Button aria-pressed={preset === value} className={preset === value ? 'primary' : ''} onClick={() => choose(value)}>{label}</Button>;
  return <YahooModal title={`Download Yahoo data for ${targets.length > 1 ? 'multiple' : `'${targets[0].symbol}'`}`} onClose={onClose} footer={<><Button onClick={onClose}>Close</Button><Button className="primary" onClick={start}>Start download</Button></>}>
    {(error || store.storageError) && <p role="alert" className="yahoo-error">{error || store.storageError}</p>}
    <fieldset><legend>Choose data range to download</legend><div className="yahoo-date-row"><label>From <TextInput aria-label="From" type="date" min={minimum} max={now} value={from} onChange={event => { setFrom(event.target.value); setPreset('custom'); setError(''); }}/></label>{presetButton('sinceLast','Since last date')}{presetButton('sixMonths','Last 6 months')}{presetButton('year','Last year')}</div><div className="yahoo-date-row"><label>To <TextInput aria-label="To" type="date" min={minimum} max={now} value={to} onChange={event => { setTo(event.target.value); setPreset('custom'); setError(''); }}/></label>{presetButton('fiveYears','Last 5 years')}{presetButton('tenYears','Last 10 years')}{presetButton('allTime','All time')}</div></fieldset>
    <fieldset><legend>Redownload options</legend><div className="yahoo-redownload"><label><input type="radio" name="yahoo-overwrite" checked={!overwrite} onChange={() => setOverwrite(false)}/> Add only missing data</label><label><input type="radio" name="yahoo-overwrite" checked={overwrite} onChange={() => setOverwrite(true)}/> Overwrite existing data</label></div></fieldset>
    <p className="yahoo-mock-note">This download is simulated. It stores date coverage metadata without contacting Yahoo or creating market bars.</p>
  </YahooModal>;
}
