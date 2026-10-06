import { Button, Field, TextInput } from '../../../../components/ui';
import { AddPopup } from '../add/addPopup';
import { datePatterns, timeframes, timezones } from '../fileImport';
import { useFilesMassImport } from './DataSourceFilesMassImportCtrl';
import '../styles.css';

export function MassImportPopup({ onClose, onStarted }: { onClose: () => void; onStarted: () => void }) {
  const { store, picker, files, folder, error, busy, close, timezone, setTimezone, timeframe, setTimeframe, dateFormat, setDateFormat, group, setGroup, policy, setPolicy, postfix, setPostfix, start, chooseFolder } = useFilesMassImport(onClose);
  return <AddPopup onClose={close} onSaved={onStarted} mass={{ busy, onSave: start, postfix: <Field label="Data postfix"><TextInput value={postfix} maxLength={100} onChange={event => setPostfix(event.target.value)}/></Field>, content: <>
    {(error || store.storageError) && <p role="alert">{error || store.storageError}</p>}
    <fieldset><div className="import-file-picker"><Field label="Source data folder"><TextInput readOnly value={folder}/></Field><Button disabled={busy} onClick={() => picker.current?.click()}>Select</Button><input hidden ref={picker} aria-label="Choose source folder" type="file" multiple {...{ webkitdirectory: '', directory: '' }} onChange={chooseFolder}/></div>{files.length > 0 && <small>{files.length} files selected</small>}
      <div className="import-grid"><Field label="Imported data timezone"><select aria-label="Imported data timezone" value={timezone} onChange={event => setTimezone(event.target.value)}>{timezones.map(([id, label]) => <option key={label} value={id}>{label}</option>)}</select></Field><Field label="Imported timeframe"><select aria-label="Imported timeframe" value={timeframe} onChange={event => setTimeframe(event.target.value)}>{timeframes.map(value => <option key={value}>{value}</option>)}</select></Field><Field label="Date format"><TextInput list="mass-date-patterns" value={dateFormat} onChange={event => setDateFormat(event.target.value)}/></Field><datalist id="mass-date-patterns">{datePatterns.map(pattern => <option key={pattern}>{pattern}</option>)}</datalist></div>
      <label><input type="checkbox" checked={group} onChange={event => setGroup(event.target.checked)}/> Create a new stockgroup from imported symbols</label>
      <div className="import-grid"><fieldset><legend>Folder/File csv format</legend><label><input type="radio" checked readOnly/> Date,Open,High,Low,Close,Volume<br/>Date,Ask,Bid,Volume - in case of tick timeframes</label></fieldset><fieldset className="import-mass-options"><legend>If data already exists</legend>{([['overwrite', 'Overwrite'], ['skip', 'Skip'], ['create', 'Create new ticker in data - adds postfix 2 or 3 etc.']] as const).map(([value, label]) => <label key={value}><input type="radio" checked={policy === value} onChange={() => setPolicy(value)}/> {label}</label>)}</fieldset></div>
    </fieldset>
  </> }}/ >;
}
