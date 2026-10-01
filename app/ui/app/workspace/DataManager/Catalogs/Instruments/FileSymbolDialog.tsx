import { useCallback, useEffect, useRef, useState, type ReactNode } from 'react';
import { Button, Field, Modal, TextInput } from '../../../../components/ui';
import { useDataManagerStore } from '../../Common/dataManagerStore';
import { useFileSymbols } from './fileSymbolsStore';
import { commissionModels, dataTypes, days, defaultCommission, effectiveInstruments, newInstrument, validateName, type CommissionModel, type FileInstrument, type Swap } from './fileSymbols';
import './fileSymbols.css';

function SwapFields({ value, onChange, onHelp }: { value: Swap; onChange: (value: Swap) => void; onHelp: () => void }) {
  return <fieldset><legend>Swap <Button onClick={onHelp}>Help</Button></legend>
    <label><input type="checkbox" checked={value.use} onChange={event => onChange({ ...value, use: event.target.checked })}/> Use</label>
    <div className="file-symbol-grid">
      <Field label="Swap type"><select disabled={!value.use} value={value.type} onChange={event => onChange({ ...value, type: event.target.value as Swap['type'] })}>{['money','points','percent'].map(type => <option key={type}>{type}</option>)}</select></Field>
      {(['long','short'] as const).map(key => <Field key={key} label={key === 'long' ? 'Long' : 'Short'}><TextInput aria-label={key === 'long' ? 'Long' : 'Short'} type="number" step="0.1" disabled={!value.use} value={value[key]} onChange={event => onChange({ ...value, [key]: event.target.valueAsNumber })}/><small>{value.type === 'money' ? '$ per day' : value.type === 'percent' ? '% per year' : 'points per day'}</small></Field>)}
      <Field label="Triple swap on"><select disabled={!value.use} value={value.tripleSwapOn} onChange={event => onChange({ ...value, tripleSwapOn: event.target.value })}>{days.map(day => <option key={day}>{day}</option>)}</select></Field>
      <Field label="Rollout hour"><TextInput disabled={!value.use} type="time" step="1800" value={value.rolloutHour} onChange={event => onChange({ ...value, rolloutHour: event.target.value })}/></Field>
    </div>
  </fieldset>;
}
const numericFields = [
  ['pointValue', 'Point value in $', 0, 1], ['tickSize', 'Pip/Tick size', 0, 0.0001], ['tickStep', 'Pip/Tick step', 0, 0.00001],
  ['spread', 'Default spread (pips)', 0, 1], ['slippage', 'Default slippage (pips)', 0, 1], ['minDistance', 'Min distance', 0, 1],
  ['multiplier', 'Order size multiplier', 1, 1], ['sizeStep', 'Order size step', 0, 1],
] as const;
export function FileSymbolDialog({ onClose, onSaved }: { onClose: () => void; onSaved: () => void }) {
  const file = useFileSymbols();
  const data = useDataManagerStore();
  const all = effectiveInstruments(file.instruments, file.overrides, file.removed);
  const brokers = [{ id: '-1', name: 'Default', postfix: '' }, ...data.brokers.filter(row => row.mtUse)];
  const [page, setPage] = useState<'symbol' | 'instrument' | 'help'>('symbol');
  const [helpOrigin, setHelpOrigin] = useState<'symbol' | 'instrument'>('symbol');
  const [symbol, setSymbol] = useState('');
  const [barType, setBarType] = useState<'start' | 'end'>('start');
  const [broker, setBroker] = useState('');
  const [selected, setSelected] = useState(all.find(row => row.type === 'Forex')?.symbol ?? all[0]?.symbol ?? '');
  const [draft, setDraft] = useState(newInstrument());
  const [swapDraft, setSwapDraft] = useState(all.find(row => row.symbol === selected)?.swap ?? newInstrument().swap);
  const [error, setError] = useState('');
  const container = useRef<HTMLDivElement>(null);
  const focusTarget = useRef<string | null>(null);
  const item = all.find(row => row.symbol === selected);
  const choices = all.filter(row => !broker || row.broker === broker);
  const shown = page === 'instrument' ? draft : item;
  useEffect(() => {
    const selector = focusTarget.current ?? 'button';
    focusTarget.current = null;
    const timer = window.setTimeout(() => container.current?.querySelector<HTMLElement>(`[role=dialog] ${selector}`)?.focus(), 0);
    return () => window.clearTimeout(timer);
  }, [page]);
  const back = useCallback(() => {
    setError('');
    if (page === 'help') { focusTarget.current = '[data-swap-help] button'; setPage(helpOrigin); }
    else if (page === 'instrument') { focusTarget.current = '[data-add-instrument]'; setPage('symbol'); }
    else onClose();
  }, [page, helpOrigin, onClose]);
  function choose(name: string) { setSelected(name); setSwapDraft(structuredClone(all.find(row => row.symbol === name)?.swap ?? newInstrument().swap)); }
  function help() { setHelpOrigin(page === 'instrument' ? 'instrument' : 'symbol'); setPage('help'); }
  async function save() {
    try {
      if (data.storageError) throw new Error(data.storageError);
      if (page === 'instrument') {
        validateName(draft.symbol, [], 'Instrument');
        const profile = brokers.find(row => row.id === draft.broker);
        const value = { ...draft, symbol: draft.symbol + (profile?.postfix ?? ''), brokerName: profile?.name ?? '' };
        await file.addInstrument(value, brokers.map(row => row.id));
        setBroker(''); setSelected(value.symbol); setSwapDraft(structuredClone(value.swap));
        focusTarget.current = '[data-add-instrument]'; setPage('symbol'); setError('');
      } else {
        if (!item) throw new Error('Choose an instrument.');
        await file.addSymbol(symbol, item, barType, []);
        onSaved(); onClose();
      }
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to save.'); }
  }
  function numberField(key: typeof numericFields[number][0], label: string, min: number, step: number) {
    const adjustedStep = key === 'tickSize' || key === 'tickStep' ? shown?.type === 'Stock' ? 0.01 : shown?.type === 'Futures' ? 0.1 : step : step;
    return <Field key={key} label={label}><TextInput disabled={page !== 'instrument'} type="number" min={min} step={adjustedStep} value={shown?.[key] ?? ''} onChange={event => setDraft({ ...draft, [key]: event.target.valueAsNumber })}/></Field>;
  }
  return <div className="file-symbol-flow" ref={container} onKeyDown={event => {
    if (event.key !== 'Tab') return;
    const controls = Array.from(container.current?.querySelectorAll<HTMLElement>('button:not(:disabled),input:not(:disabled),select:not(:disabled)') ?? []);
    if (event.shiftKey && document.activeElement === controls[0]) { event.preventDefault(); controls.at(-1)?.focus(); }
    else if (!event.shiftKey && document.activeElement === controls.at(-1)) { event.preventDefault(); controls[0]?.focus(); }
  }}><Modal key={page} title={page === 'help' ? 'Commission & Swap Explanation' : page === 'instrument' ? 'Add instrument' : 'Add symbol'} onClose={back} width={page === 'help' ? 800 : 700} footer={<><Button onClick={back}>Close</Button>{page !== 'help' && <Button className="primary" onClick={save}>Save</Button>}</>}>
    {(error || file.storageError) && <p role="alert" className="file-symbol-error">{error || file.storageError}</p>}
    {page === 'help' ? <div className="file-symbol-help"><p>In MetaTrader 4 and 5, a swap is the interest rate charged or paid for holding a trading position overnight. If the interest rate on the currency you are buying is higher than the interest rate on the currency you are selling, you will earn a positive swap. If the interest rate on the currency you are buying is lower than the interest rate on the currency you are selling, you will incur a negative swap. The swap rate varies depending on the currency pair and broker. It can affect your trading profitability, so it's important to be aware of the swap rates for the currency pairs you trade.</p><p>Positive swap: If you are long on the AUD/JPY currency pair and the interest rate on the Australian dollar is higher than the interest rate on the Japanese yen, you will earn a positive swap. This means that you will receive a small amount of money in your trading account for holding the position overnight.</p><p>Negative swap: If you are short on the EUR/USD currency pair and the interest rate on the euro is lower than the interest rate on the US dollar, you will incur a negative swap. This means that you will have to pay a small amount of money from your trading account for holding the position overnight.</p><p>The swap is calculated on a daily basis at 11pm (Rollover time). If you have any trades that were opened after 11pm, they will not incur any swap charges until the next day's 11pm calculation.</p></div> : <>
      {page === 'symbol' && <>
        <fieldset><legend>Data settings</legend><Field label="Data symbol name"><TextInput value={symbol} maxLength={128} onChange={event => setSymbol(event.target.value)}/></Field>
          <div><h3>Data type</h3><div className="file-symbol-radios">
            <label><input type="radio" name="file-bar-type" checked={barType === 'start'} onChange={() => setBarType('start')}/> Timestamp is start of bar time (MetaTrader, Dukascopy, forex data)</label>
            <label><input type="radio" name="file-bar-type" checked={barType === 'end'} onChange={() => setBarType('end')}/> Timestamp is end of bar time (NinjaTrader, Tradestation, futures data)</label>
          </div></div>
        </fieldset>
        <fieldset><legend>Choose instrument</legend><p>Instrument is a specification of this symbol - it contains tick size, point value etc.</p><p>You can have multiple data imported - for example EURUSD_1, EURUSD_2, EURUSD_3, but they share the same instrument specification for EURUSD.</p>
          <div className="file-symbol-chooser"><Field label="Broker profile filter"><select value={broker} onChange={event => { setBroker(event.target.value); choose(all.find(row => !event.target.value || row.broker === event.target.value)?.symbol ?? ''); }}><option value="">All broker profiles</option>{brokers.map(row => <option value={row.id} key={row.id}>{row.name}</option>)}</select></Field>
          <Field label="Instrument"><select aria-label="Instrument" value={selected} onChange={event => choose(event.target.value)}>{!choices.length && <option value="">No instruments</option>}{choices.map(row => <option key={row.symbol}>{row.symbol}</option>)}</select></Field>
          <Button data-add-instrument onClick={() => { setDraft(newInstrument()); setError(''); setPage('instrument'); }}>⊕ Add new instrument</Button></div>
        </fieldset>
      </>}
      <fieldset><legend>Instrument details</legend><div className="file-symbol-grid">
        <Field label="Broker profile"><select aria-label="Broker profile" disabled={page !== 'instrument'} value={shown?.broker ?? '-1'} onChange={event => setDraft({ ...draft, broker: event.target.value })}>{brokers.map(row => <option value={row.id} key={row.id}>{row.name}</option>)}</select></Field>
        <Field label="Instrument name"><TextInput aria-label="Instrument name" disabled={page !== 'instrument'} value={shown?.symbol ?? ''} maxLength={128} onChange={event => setDraft({ ...draft, symbol: event.target.value })}/>{page === 'instrument' && <small>{brokers.find(row => row.id === draft.broker)?.postfix}</small>}</Field>
        <Field label="Data type"><select aria-label="Data type" disabled={page !== 'instrument'} value={shown?.type ?? 'Forex'} onChange={event => setDraft({ ...draft, type: event.target.value })}>{dataTypes.map(type => <option key={type}>{type}</option>)}</select></Field>
        <Field label="Description"><TextInput disabled={page !== 'instrument'} value={shown?.name ?? ''} onChange={event => setDraft({ ...draft, name: event.target.value })}/></Field>
        {numericFields.map(([key,label,min,step]) => numberField(key,label,min,step))}
      </div></fieldset>
      {page === 'instrument' && <fieldset><legend>Default commissions model</legend>
        <Field label="Commission model"><select aria-label="Commission model" value={draft.commission.model} onChange={event => setDraft({ ...draft, commission: defaultCommission(event.target.value as CommissionModel) })}>{commissionModels.map(model => <option key={model}>{model}</option>)}</select></Field>
        {draft.commission.model !== 'None' && <div className="file-symbol-grid">
          <Field label="Commission"><TextInput type="number" min={draft.commission.model === 'Stockpicker' ? 0 : draft.commission.model === 'Percentage based' ? -100 : -100000} max={draft.commission.model === 'Percentage based' ? 100 : 100000} step="any" value={draft.commission.value} onChange={event => setDraft({ ...draft, commission: { ...draft.commission, value: event.target.valueAsNumber } })}/></Field>
          {draft.commission.model === 'Stockpicker' && <>
            <Field label="Commission type"><select value={draft.commission.unit} onChange={event => setDraft({ ...draft, commission: { ...draft.commission, unit: event.target.value } })}><option value="share">$ per share</option><option value="order">$ per order</option><option value="equity">% of trade value</option></select></Field>
            {(['min','max'] as const).map(key => <Field key={key} label={key === 'min' ? 'Min per order' : 'Max per order'}><TextInput type="number" min="0" max="100000" step="any" value={draft.commission[key]} onChange={event => setDraft({ ...draft, commission: { ...draft.commission, [key]: event.target.valueAsNumber } })}/></Field>)}
            {(['minUnit','maxUnit'] as const).map(key => <Field key={key} label={key === 'minUnit' ? 'Min per order type' : 'Max per order type'}><select value={draft.commission[key]} onChange={event => setDraft({ ...draft, commission: { ...draft.commission, [key]: event.target.value } })}><option value="money">$</option><option value="equity">% of trade value</option></select></Field>)}
          </>}
        </div>}
      </fieldset>}
      <div data-swap-help><SwapFields value={page === 'instrument' ? draft.swap : swapDraft} onChange={swap => page === 'instrument' ? setDraft({ ...draft, swap }) : setSwapDraft(swap)} onHelp={help}/></div>
    </>}
  </Modal></div>;
}
