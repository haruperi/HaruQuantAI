import { useRef, useState } from 'react';
import { Button, Field, Modal, TextInput } from '../../../../components/ui';
import { newSymbol, type FileSymbol, type SymbolBroker, type SymbolMassPatch } from '../../FileImport/fileSymbols';
import { commissionInfo, type CatalogSymbol } from './symbolsApiClient';
import { useSymbols } from './symbolsStore';
import { SymbolDetailsFields } from './SymbolDetailsFields';
import './symbols.css';

export function SymbolsModal({ mode, selected, brokers, onClose, onSaved }: {
  mode: 'add' | 'edit' | 'mass' | 'clone'; selected: CatalogSymbol[];
  brokers: SymbolBroker[]; onClose: () => void; onSaved: (message: string) => void;
}) {
  const [draft, setDraft] = useState<FileSymbol>(() => selected[0] ? structuredClone(selected[0]) : { ...newSymbol(), contractSize: 100000, pipSize: 0.0001, marginRate: 0.05, decimals: 5, minVolume: 0.01, maxVolume: 100, lotStep: 0.01, tickValue: 10 });
  const [flags, setFlags] = useState<SymbolMassPatch['fields']>({});
  const [name, setName] = useState(selected[0] ? selected[0].symbol + 'Clone' : '');
  const [error, setError] = useState('');
  const [datasource, setDatasource] = useState('SQ default');
  const [pending, setPending] = useState(false);
  const submitting = useRef(false);
  const title = { add: 'Add symbol', edit: 'Edit symbol', mass: 'Mass-Edit symbol', clone: 'Clone symbol' }[mode];
  const close = () => { if (!submitting.current) onClose(); };
  async function save() {
    if (submitting.current) return;
    submitting.current = true; setPending(true); setError('');
    try {
      const store = useSymbols.getState();
      if (mode === 'add') {
        if (!datasource.trim()) throw new Error('Enter a datasource / broker profile suffix.');
        if (!(Number(draft.contractSize) > 0) || !(Number(draft.pipSize) > 0)) throw new Error('Enter positive contract and pip sizes.');
        const profile = brokers.find(row => row.id === draft.broker);
        await store.addSymbolDefinition({ ...draft, symbol: draft.symbol + (profile?.postfix ?? '') }, datasource.trim());
      } else if (mode === 'clone') await store.cloneSymbol(selected[0], name);
      else if (mode === 'edit') await store.editSymbol(selected[0], draft);
      else await store.massEditSymbols(selected.map(row => row.id), { fields: flags, value: draft });
      onSaved(mode === 'clone' ? 'Symbol cloned.' : mode === 'add' ? 'Symbol added.' : 'Symbols modified.');
      onClose();
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to save symbol.'); }
    finally { submitting.current = false; setPending(false); }
  }
  const commission = selected[0] ? commissionInfo(selected[0].record.commissions) : null;
  const choices = [...brokers];
  if (!choices.some(row => row.id === draft.broker)) choices.push({ id: draft.broker, name: draft.brokerName, timezone: draft.timezone, postfix: '' });
  return <div className="symbols-flow"><Modal title={title} width={720} onClose={close} footer={<><Button disabled={pending} onClick={close}>Close</Button><Button disabled={pending} className="primary" onClick={() => void save()}>{pending ? 'Saving…' : 'Save'}</Button></>}>
    {error && <p className="symbol-error" role="alert">{error}</p>}
    {pending && <p role="status">Saving symbol specifications…</p>}
    <fieldset className="symbol-form-body" disabled={pending}>
      {mode === 'add' && <Field label="Datasource suffix"><TextInput value={datasource} onChange={event => setDatasource(event.target.value)}/></Field>}
      {mode === 'clone' ? <><p>Copy the complete saved specification for {selected[0].symbol}, retaining its broker profile.</p><Field label="New symbol name"><TextInput value={name} maxLength={128} onChange={event => setName(event.target.value)}/></Field></> : <>
        {selected[0]?.record.swap_settings === null && <p>Legacy swap type and rollover time are unspecified. Editing swap settings explicitly configures them.</p>}
        {commission && <p title={commission.details}>{commission.summary}. Other edits preserve commission settings.</p>}
        <SymbolDetailsFields value={draft} onChange={setDraft} brokers={choices} identityLocked={mode === 'edit'} massFlags={mode === 'mass' ? flags : undefined} onMassFlags={setFlags}/>
      </>}
    </fieldset>
  </Modal></div>;
}
