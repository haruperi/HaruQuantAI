import { useEffect, useState } from 'react';
import { Button, Checkbox, Field, Modal, TextInput } from '../../../../components/ui';
import { commissionModels, dataTypes, days, defaultCommission, newInstrument, type CommissionModel, type FileInstrument, type InstrumentBroker, type InstrumentMassPatch, type Swap } from '../../FileImport/fileSymbols';
import './instruments.css';

const numeric = [
  ['pointValue','Point value in $',0], ['tickSize','Pip/Tick size',0], ['tickStep','Pip/Tick step',0],
  ['spread','Default spread * pips',0], ['slippage','Default slippage * pips',0], ['minDistance','Min distance',0],
  ['multiplier','Order size multiplier',1], ['sizeStep','Order size step',0],
] as const;

function SwapEditor({ value, disabled, onChange, onHelp }: { value: Swap; disabled?: boolean; onChange: (value: Swap) => void; onHelp: () => void }) {
  return <fieldset><legend>Swap <Button type="button" onClick={onHelp}>Help</Button></legend>
    <Checkbox label="Use" checked={value.use} disabled={disabled} onChange={use => onChange({ ...value, use })}/>
    <div className="instrument-fields two">
      <Field label="Swap type"><select disabled={disabled || !value.use} value={value.type} onChange={event => onChange({ ...value, type:event.target.value as Swap['type'] })}><option>money</option><option>points</option><option>percent</option></select></Field>
      <Field label="Triple swap on"><select disabled={disabled || !value.use} value={value.tripleSwapOn} onChange={event => onChange({ ...value, tripleSwapOn:event.target.value })}>{days.map(day => <option key={day}>{day}</option>)}</select></Field>
      <Field label="Long"><TextInput aria-label="Swap Long" disabled={disabled || !value.use} type="number" step="0.1" value={value.long} onChange={event => onChange({ ...value, long:event.target.valueAsNumber })}/><small>{value.type === 'percent' ? '% per year' : value.type === 'money' ? '$ per day' : 'points per day'}</small></Field>
      <Field label="Short"><TextInput aria-label="Swap Short" disabled={disabled || !value.use} type="number" step="0.1" value={value.short} onChange={event => onChange({ ...value, short:event.target.valueAsNumber })}/></Field>
      <Field label="Rollout hour"><TextInput disabled={disabled || !value.use} type="time" step="1800" value={value.rolloutHour} onChange={event => onChange({ ...value, rolloutHour:event.target.value })}/></Field>
    </div>
  </fieldset>;
}

export function InstrumentDetailsFields({ value, onChange, brokers, identityLocked = false, massFlags, onMassFlags }: {
  value: FileInstrument; onChange: (value: FileInstrument) => void; brokers: InstrumentBroker[]; identityLocked?: boolean;
  massFlags?: InstrumentMassPatch['fields']; onMassFlags?: (value: InstrumentMassPatch['fields']) => void;
}) {
  const [help, setHelp] = useState(false); const mass = Boolean(massFlags);
  useEffect(() => {
    if (!help) return;
    const closeTopmost = (event: KeyboardEvent) => {
      if (event.key !== 'Escape') return;
      event.stopImmediatePropagation(); setHelp(false);
    };
    document.addEventListener('keydown', closeTopmost, true);
    return () => document.removeEventListener('keydown', closeTopmost, true);
  }, [help]);
  const enabled = (key: keyof InstrumentMassPatch['fields']) => !mass || Boolean(massFlags?.[key]);
  const flag = (key: keyof InstrumentMassPatch['fields'], label: string) => mass && <Checkbox label={`Change ${label}`} checked={Boolean(massFlags?.[key])} onChange={checked => onMassFlags?.({ ...massFlags, [key]:checked })}/>;
  function changeType(type: string): void { const defaults = newInstrument(type); onChange({ ...value, type, pointValue:defaults.pointValue, tickSize:defaults.tickSize, tickStep:defaults.tickStep, spread:defaults.spread, slippage:defaults.slippage, commission:defaults.commission }); }
  return <div className="instrument-details-flow">
    <fieldset><legend>Instrument details</legend><div className="instrument-fields two">
      {!mass && <><Field label="Broker profile *"><select disabled={identityLocked} value={value.broker} onChange={event => onChange({ ...value, broker:event.target.value, brokerName:brokers.find(row => row.id === event.target.value)?.name ?? '' })}>{brokers.map(row => <option value={row.id} key={row.id}>{row.name}</option>)}</select></Field>
      <Field label="Instrument *"><TextInput aria-label="Instrument" disabled={identityLocked} maxLength={128} value={value.symbol} onChange={event => onChange({ ...value, symbol:event.target.value })}/><small>{brokers.find(row => row.id === value.broker)?.postfix}</small></Field>
      <Field label="Description"><TextInput value={value.name} onChange={event => onChange({ ...value, name:event.target.value })}/></Field></>}
      <div className="instrument-option">{flag('type','Data type')}<Field label="Data type *"><select disabled={!enabled('type')} value={value.type} onChange={event => changeType(event.target.value)}>{dataTypes.map(type => <option key={type}>{type}</option>)}</select></Field></div>
      {numeric.map(([key,label,min]) => <div className="instrument-option" key={key}>{flag(key,label)}<Field label={label}><TextInput disabled={!enabled(key)} type="number" min={min} step={key === 'tickSize' ? value.type === 'Stock' ? .01 : value.type === 'Futures' ? .1 : .0001 : key === 'tickStep' ? value.type === 'Stock' ? .01 : value.type === 'Futures' ? .1 : .00001 : 1} value={value[key]} onChange={event => onChange({ ...value, [key]:event.target.valueAsNumber })}/></Field></div>)}
    </div></fieldset>
    <div className="instrument-option">{flag('commission','default commission model')}<fieldset disabled={!enabled('commission')}><legend>Default commissions model</legend>
      <Field label="Commission model"><select value={value.commission.model} onChange={event => onChange({ ...value, commission:defaultCommission(event.target.value as CommissionModel) })}>{commissionModels.map(model => <option key={model}>{model}</option>)}</select></Field>
      {value.commission.model !== 'None' && <div className="instrument-fields two"><Field label="Commission"><TextInput type="number" step="any" value={value.commission.value} onChange={event => onChange({ ...value, commission:{ ...value.commission, value:event.target.valueAsNumber } })}/></Field>
        {value.commission.model === 'Stockpicker' && <><Field label="Commission type"><select value={value.commission.unit} onChange={event => onChange({ ...value, commission:{ ...value.commission, unit:event.target.value } })}><option value="share">$ per share</option><option value="order">$ per order</option><option value="equity">% of trade value</option></select></Field>
        <Field label="Min per order"><TextInput type="number" min="0" value={value.commission.min} onChange={event => onChange({ ...value, commission:{ ...value.commission, min:event.target.valueAsNumber } })}/></Field><Field label="Min per order type"><select value={value.commission.minUnit} onChange={event => onChange({ ...value, commission:{ ...value.commission, minUnit:event.target.value } })}><option value="money">$</option><option value="equity">% of trade value</option></select></Field>
        <Field label="Max per order"><TextInput type="number" min="0" value={value.commission.max} onChange={event => onChange({ ...value, commission:{ ...value.commission, max:event.target.valueAsNumber } })}/></Field><Field label="Max per order type"><select value={value.commission.maxUnit} onChange={event => onChange({ ...value, commission:{ ...value.commission, maxUnit:event.target.value } })}><option value="money">$</option><option value="equity">% of trade value</option></select></Field></>}
      </div>}
    </fieldset></div>
    <div className="instrument-option">{flag('swap','swap')}<SwapEditor value={value.swap} disabled={!enabled('swap')} onChange={swap => onChange({ ...value, swap })} onHelp={() => setHelp(true)}/></div>
    {help && <Modal title="Commission & Swap Explanation" width={800} onClose={() => setHelp(false)} footer={<Button onClick={() => setHelp(false)}>Close</Button>}><div className="instrument-help"><p>In MetaTrader 4 and 5, a swap is the interest rate charged or paid for holding a trading position overnight. A positive rate credits the account; a negative rate charges it.</p><p>The rate varies by instrument and broker and can affect profitability. It is calculated daily at the configured rollover time. Positions opened after rollover begin accruing on the following calculation.</p></div></Modal>}
  </div>;
}
