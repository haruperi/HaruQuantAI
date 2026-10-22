import { useRef, useState } from 'react';
import { Button, Field, Modal, TextInput } from '../../../../components/ui';
import { timezones } from '../../FileImport/fileImport';
import { commissionModels, defaultCommission, type Commission } from '../../FileImport/fileSymbols';
import { useDataManagerStore } from '../../Common/dataManagerStore';
import type { BrokerProfile } from './brokerProfiles';
import './brokerProfiles.css';

export function BrokerProfilesModal({mode,source,canSetStockPicker,canSetMt,canSetTimezone,onClose,onSaved}:{mode:'add'|'edit';source?:BrokerProfile;canSetStockPicker:boolean;canSetMt:boolean;canSetTimezone:boolean;onClose:()=>void;onSaved:(message:string)=>void}) {
  const [value,setValue] = useState<BrokerProfile>(() => source ? structuredClone(source) : {id:'',name:'',desc:'',postfix:'',timezone:'UTC',mtUse:true,stockPickerUse:true,system:false,stocks:[],instruments:[],spreadModel:{model:'inherit'},commissionModel:{model:'inherit'}});
  const [error,setError] = useState('');
  const [pending,setPending] = useState(false);
  const submitting = useRef(false);
  const commission = value.commissionModel ?? {model:'inherit' as const};
  const spread = value.spreadModel ?? {model:'inherit' as const};
  function changeCommission(updates: Partial<Commission>) { if (commission.model !== 'inherit') setValue({...value,commissionModel:{...commission,...updates}}); }
  function close() { if (!submitting.current) onClose(); }
  async function save() {
    if (submitting.current) return;
    submitting.current = true; setPending(true); setError('');
    try {
      await useDataManagerStore.getState().saveBroker(value);
      onSaved(mode === 'add' ? 'Broker was added' : 'Broker was updated'); onClose();
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Cannot save broker.'); }
    finally { submitting.current = false; setPending(false); }
  }
  return <div className="broker-flow"><Modal title={`${mode === 'add' ? 'Add' : 'Edit'} Broker profile`} width={700} onClose={close} footer={<><Button disabled={pending} onClick={close}>Close</Button><Button disabled={pending} className="primary" onClick={() => void save()}>{pending ? 'Saving…' : 'Save'}</Button></>}>
    {error && <p className="broker-error" role="alert">{error}</p>}
    <fieldset disabled={pending}><Field label="Broker profile name *"><TextInput aria-label="Broker profile name" maxLength={50} value={value.name} onChange={e => setValue({...value,name:e.target.value})}/></Field><Field label="Description"><textarea aria-label="Broker description" maxLength={250} value={value.desc} onChange={e => setValue({...value,desc:e.target.value})}/></Field></fieldset>
    <fieldset disabled={pending}><legend>Stockpicker functionality</legend><label className="broker-check"><input aria-label="Enable stock filtering" type="checkbox" checked={value.stockPickerUse} disabled={!canSetStockPicker} onChange={e => setValue({...value,stockPickerUse:e.target.checked})}/>Use this broker profile for filtering stocks</label></fieldset>
    <fieldset disabled={pending}><legend>Instrument and session settings</legend><label className="broker-check"><input aria-label="Enable instrument settings" type="checkbox" checked={value.mtUse} disabled={!canSetMt} onChange={e => setValue({...value,mtUse:e.target.checked})}/>Use this profile for instruments and sessions</label><Field label="Broker timezone"><select aria-label="Broker timezone" disabled={!canSetTimezone} value={value.timezone} onChange={e => setValue({...value,timezone:e.target.value})}>{timezones.map(([id,label]) => <option key={`${id}-${label}`} value={id}>{label}</option>)}</select></Field><Field label="Instrument/data postfix"><TextInput aria-label="Instrument data postfix" maxLength={100} value={value.postfix} onChange={e => setValue({...value,postfix:e.target.value})}/></Field></fieldset>
    <fieldset disabled={pending}><legend>Configured cost defaults</legend><p className="broker-note">Defaults apply only when selected during instrument import. Existing symbols and retrieved broker fees keep their settings.</p>
      <Field label="Spread model"><select aria-label="Broker spread model" value={spread.model} onChange={e => setValue({...value,spreadModel:e.target.value === 'fixed' ? {model:'fixed',value:0} : {model:'inherit'}})}><option value="inherit">Use instrument spread</option><option value="fixed">Fixed spread</option></select></Field>
      {spread.model === 'fixed' && <Field label="Spread value (instrument units)"><input aria-label="Broker spread value" type="number" min={0} max={100000} step="any" value={spread.value} onChange={e => setValue({...value,spreadModel:{model:'fixed',value:e.target.valueAsNumber}})}/></Field>}
      <Field label="Commission model"><select aria-label="Broker commission model" value={commission.model} onChange={e => setValue({...value,commissionModel:e.target.value === 'inherit' ? {model:'inherit'} : defaultCommission(e.target.value as Commission['model'])})}><option value="inherit">Use instrument commission</option>{commissionModels.map(model => <option key={model}>{model}</option>)}</select></Field>
      {commission.model !== 'inherit' && <><Field label="Commission value"><input aria-label="Broker commission value" type="number" min={0} max={commission.model === 'Percentage based' ? 100 : 100000} step="any" disabled={commission.model === 'None'} value={commission.value} onChange={e => changeCommission({value:e.target.valueAsNumber})}/></Field>
        {commission.model === 'Stockpicker' && <><Field label="Commission basis"><select aria-label="Broker commission basis" value={commission.unit} onChange={e => changeCommission({unit:e.target.value})}>{['share','order','equity'].map(unit => <option key={unit}>{unit}</option>)}</select></Field>{(['min','max'] as const).map(key => <Field key={key} label={key === 'min' ? 'Minimum commission' : 'Maximum commission'}><div className="broker-cost-bound"><input aria-label={`Broker commission ${key}`} type="number" min={0} max={100000} step="any" value={commission[key]} onChange={e => changeCommission({[key]:e.target.valueAsNumber})}/><select aria-label={`Broker commission ${key} unit`} value={commission[`${key}Unit`]} onChange={e => changeCommission({[`${key}Unit`]:e.target.value})}>{['money','equity'].map(unit => <option key={unit}>{unit}</option>)}</select></div></Field>)}</>}
      </>}
    </fieldset>
  </Modal></div>;
}
