import { useCallback, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { CircleHelp, PlusCircle } from 'lucide-react';
import { Button, Field, Modal, TextInput } from '../../../../common/components/ui';
import { SymbolsModal } from '../Catalogs/Symbols/SymbolsModal';
import { useSymbols } from '../Catalogs/Symbols/symbolsStore';
import { days, type SymbolBroker } from '../FileImport/fileSymbols';
import { useDataManagerStore, type MockDefinition } from './dataManagerStore';
import './datasetEditDialog.css';

const specificationFields = [
  ['tickSize', 'Pip/Tick size *'], ['pointValue', 'Point value in $ *'],
  ['tickStep', 'Pip/Tick step *'], ['spread', 'Default spread * pips'],
  ['slippage', 'Default slippage * pips'], ['minDistance', 'Min distance'],
  ['multiplier', 'Order size multiplier'], ['sizeStep', 'Order size step'],
] as const;

function RecordedField({ label, value }: { label: string; value: string | number | undefined | null }) {
  return <Field label={label}><TextInput disabled readOnly value={value ?? 'Not recorded'}/></Field>;
}

export function DatasetEditDialog({ row, onClose }: { row: MockDefinition; onClose: () => void }) {
  const [name, setName] = useState(row.symbol);
  // Null keeps automatic resolution active until the user makes an explicit choice.
  const [instrumentChoice, setInstrumentId] = useState<string | null>(row.symbol_definition_id == null ? null : String(row.symbol_definition_id));
  const [brokerFilter, setBrokerFilter] = useState('all');
  const [pending, setPending] = useState(false);
  const [error, setError] = useState('');
  const [creating, setCreating] = useState(false);
  const [help, setHelp] = useState(false);
  const submitting = useRef(false);
  const beforeCreation = useRef(new Set<string>());
  const symbols = useSymbols(state => state.symbols);
  const loaded = useSymbols(state => state.loaded);
  const loading = useSymbols(state => state.isSyncing);
  const catalogueError = useSymbols(state => state.error);
  const profiles = useDataManagerStore(state => state.brokers);
  const brokers: SymbolBroker[] = profiles.map(profile => ({ id: profile.id, name: profile.name, postfix: profile.postfix, timezone: profile.timezone }));
  if (!brokers.some(broker => broker.id === '-1')) brokers.unshift({ id: '-1', name: 'Default', postfix: '', timezone: 'UTC' });
  for (const item of symbols) {
    if (!brokers.some(broker => broker.id === item.broker)) brokers.push({ id: item.broker, name: item.brokerName, postfix: '', timezone: item.timezone });
  }
  const identity = (value: string) => value.trim().replace(/^\[\[(.*)\]\]$/, '$1').trim().toLowerCase();
  const datasetBrokerNames = new Set([row.broker, row.brokerName].map(identity).filter(Boolean));
  const datasetBrokerIds = /^-?\d+$/.test(row.broker.trim())
    ? new Set([row.broker.trim()])
    : new Set(brokers.filter(broker => datasetBrokerNames.has(identity(broker.name)) || datasetBrokerNames.has(identity(broker.id))).map(broker => broker.id));
  const datasetNames = new Set([row.symbolDefinition, row.symbol, row.underlying].map(identity).filter(Boolean));
  const matches = loaded && !loading && !catalogueError ? symbols.filter(item =>
    datasetBrokerIds.has(item.broker) && datasetNames.has(identity(item.symbol))) : [];
  const instrumentId = instrumentChoice ?? (matches.length === 1 ? matches[0].id : '');
  const instrument = symbols.find(item => item.id === instrumentId);
  const unresolved = instrumentChoice === null && matches.length !== 1;
  const brokerName = instrument ? brokers.find(broker => broker.id === instrument.broker)?.name ?? instrument.brokerName : row.brokerName;
  const choices = symbols.filter(item => brokerFilter === 'all' || item.broker === brokerFilter);
  const swap = instrument?.record.swap_settings;
  const barType = row.barType === 'start' || row.barType === 'Start of bar'
    ? 'Timestamp represents start of bar time (MetaTrader, Dukascopy, forex data)'
    : row.barType === 'end' || row.barType === 'End of bar'
      ? 'Timestamp represents end of bar time (NinjaTrader, Tradestation, futures data)'
      : row.barType ?? 'Not recorded';
  const close = useCallback(() => {
    if (submitting.current) return;
    if (help) setHelp(false);
    else onClose();
  }, [help, onClose]);

  async function save() {
    if (submitting.current) return;
    setError('');
    if (!name.trim()) { setError('Enter a data symbol name.'); return; }
    if (!loaded || loading || catalogueError || unresolved || (instrumentId && !instrument)) {
      setError('Load the instrument catalogue and choose an available instrument before saving.'); return;
    }
    submitting.current = true; setPending(true);
    try {
      await useDataManagerStore.getState().editDataset(row.id, {
        ...row, symbol: name.trim(), symbol_definition_id: instrumentId ? Number(instrumentId) : null,
      });
      onClose();
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to save dataset settings.'); }
    finally { submitting.current = false; setPending(false); }
  }

  if (creating) return createPortal(<SymbolsModal mode="add" selected={[]} brokers={brokers} onClose={() => setCreating(false)} onSaved={() => {
    const created = useSymbols.getState().symbols.find(item => !beforeCreation.current.has(item.id));
    if (created) { setInstrumentId(created.id); setBrokerFilter('all'); }
    setCreating(false);
  }}/>, document.body);

  return createPortal(<div className="dataset-edit-flow" onKeyDown={event => {
    if (event.key !== 'Tab') return;
    const controls = Array.from(event.currentTarget.querySelectorAll<HTMLElement>('button:not(:disabled),input:not(:disabled),select:not(:disabled),textarea:not(:disabled),a[href]'));
    if (event.shiftKey && document.activeElement === controls[0]) { event.preventDefault(); controls.at(-1)?.focus(); }
    else if (!event.shiftKey && document.activeElement === controls.at(-1)) { event.preventDefault(); controls[0]?.focus(); }
  }}><Modal title={help ? 'Swap explanation' : 'Edit symbol'} width={700} className="dataset-edit-modal" onClose={close} footer={<>
    <Button disabled={pending} onClick={close}>Close</Button>
    {!help && <Button className="primary" disabled={pending || loading || !loaded || Boolean(catalogueError) || unresolved || Boolean(instrumentId && !instrument)} onClick={() => void save()}>{pending ? 'Saving…' : 'Save'}</Button>}
  </>}>
    {help ? <section className="dataset-edit-help"><h3>Swap</h3><p>Swap is the charge or credit for holding a position overnight. Long and short values apply to their respective position directions.</p><p>Points and money are charged per day; percent is an annual rate. The selected instrument defines the triple-swap day and rollover time.</p><p>These are shared instrument settings. This dataset editor displays their saved values without changing them.</p></section> : <>
      {error && <p className="dataset-edit-error" role="alert">{error}</p>}
      <section className="dataset-edit-section" aria-label="Data settings"><h3>Data settings</h3><div className="dataset-edit-settings">
        <Field label="Data symbol name"><TextInput value={name} maxLength={128} disabled={pending} onChange={event => setName(event.target.value)}/></Field>
        <RecordedField label="Bar type" value={barType}/><RecordedField label="Timezone" value={row.timezone}/>
      </div></section>
      <section className="dataset-edit-section" aria-label="Choose instrument"><h3>Choose instrument</h3>
        <p className="dataset-edit-hint">Instrument is a specification of this symbol — it contains tick size, point value, etc.<br/>You can have multiple datasets for a symbol; they can share the same instrument specification.</p>
        {loading && <p role="status">Loading instrument catalogue…</p>}
        {catalogueError && <p className="dataset-edit-error" role="alert">{catalogueError} <Button disabled={loading || pending} onClick={() => void useSymbols.getState().refreshFromServer(brokers)}>Retry instruments</Button></p>}
        <div className="dataset-edit-picker"><span>Instrument *</span>
          <select aria-label="Filter instruments by broker" disabled={pending || loading} value={brokerFilter} onChange={event => setBrokerFilter(event.target.value)}><option value="all">All broker profiles</option>{brokers.map(broker => <option key={broker.id} value={broker.id}>{broker.name}</option>)}</select>
          <select aria-label="Instrument" disabled={pending || loading || !loaded || Boolean(catalogueError)} value={unresolved ? '__unresolved__' : instrumentId} onChange={event => setInstrumentId(event.target.value)}>{unresolved && <option value="__unresolved__" disabled>Choose instrument</option>}<option value="">No instrument</option>{instrumentId && !instrument && <option value={instrumentId}>Unavailable instrument (ID {instrumentId})</option>}{instrument && !choices.includes(instrument) && <option value={instrument.id}>{instrument.symbol} (current selection)</option>}{choices.map(item => <option key={item.id} value={item.id}>{item.symbol}</option>)}</select>
          <button className="dataset-edit-link" disabled={pending || loading || !loaded || Boolean(catalogueError)} onClick={() => { beforeCreation.current = new Set(symbols.map(item => item.id)); setCreating(true); }}><PlusCircle size={14} aria-hidden="true"/>Add new instrument</button>
        </div>
        {loaded && !loading && !catalogueError && !instrument && <p className="dataset-edit-hint">{instrumentId ? 'The linked instrument is unavailable. Select a saved instrument or explicitly choose No instrument.' : unresolved ? matches.length > 1 ? 'Multiple instruments match this dataset in its broker profile. Choose the intended instrument.' : 'No exact instrument match was found in this dataset’s broker profile. Choose an instrument or explicitly choose No instrument.' : 'No instrument selected. Choose one to view its saved specification.'}</p>}
      </section>
      <section className="dataset-edit-section" aria-label="Instrument details" title="Shared instrument details are read-only. COT is not supplied by this catalogue."><div className="dataset-edit-grid">
        <RecordedField label="Broker profile *" value={brokerName}/><RecordedField label="Instrument *" value={instrument?.symbol ?? row.symbolDefinition}/><span className="dataset-edit-spacer"/>
        <RecordedField label="Data type *" value={instrument?.type ?? row.category}/><div className="dataset-edit-description"><RecordedField label="Description" value={instrument?.name}/></div>
        {specificationFields.map(([key, label]) => <RecordedField key={key} label={label} value={instrument?.[key]}/>)}
        <RecordedField label="COT" value={null}/>
      </div></section>
      <section className="dataset-edit-section" aria-label="Swap"><div className="dataset-edit-swap-header"><h3>Swap</h3><Button onClick={() => setHelp(true)}><CircleHelp size={14} aria-hidden="true"/>Help</Button></div>
        <label className="dataset-edit-toggle"><input type="checkbox" disabled checked={swap?.use ?? false}/><span>Use</span></label>
        <div className="dataset-edit-swap-fields"><RecordedField label="Swap type" value={swap?.type}/>
          <RecordedField label="Long" value={swap?.long ?? instrument?.record.swap_long}/><span>{swap ? swap.type === 'percent' ? '% per year' : swap.type === 'money' ? '$ per day' : 'points per day' : 'Unit not recorded'}</span>
          <RecordedField label="Short" value={swap?.short ?? instrument?.record.swap_short}/><span>{swap ? swap.type === 'percent' ? '% per year' : swap.type === 'money' ? '$ per day' : 'points per day' : 'Unit not recorded'}</span>
          <RecordedField label="Triple swap on" value={swap?.tripleSwapOn ?? (instrument ? days[instrument.record.swap_3day_day] : undefined)}/><RecordedField label="Rollout hour" value={swap?.rolloutHour}/>
        </div>
        {!swap && <p className="dataset-edit-note">Use, swap type and rollout hour were not recorded. No defaults have been applied.</p>}
      </section>
    </>}
  </Modal></div>, document.body);
}
