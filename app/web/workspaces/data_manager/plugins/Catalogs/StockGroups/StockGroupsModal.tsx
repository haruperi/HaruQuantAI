import { useState } from 'react';
import { Button, Field, Modal, TextInput } from '../../../../../common/components/ui';
import { useStockGroups } from './stockGroupsStore';
import { editStockGroupCatalog } from './stockGroupApiClient';
import type { StockGroupDefinition } from './stockGroups';
import './stockGroups.css';

export function StockGroupsModal({ mode, source, selected, onClose, onSaved }: { mode: 'add'|'edit'; source?: StockGroupDefinition; selected?:StockGroupDefinition[]; onClose: () => void; onSaved: (message: string, item: StockGroupDefinition) => void }) {
  const [name, setName] = useState(source?.name ?? ''); const [description, setDescription] = useState(source?.description ?? ''); const [error, setError] = useState('');
  const [pending,setPending]=useState(false);
  const save = async () => { if(pending)return;setPending(true);try { const item = selected?.length ? (await editStockGroupCatalog(selected.map(row=>row.id),{description}))[0] : await useStockGroups.getState().saveGroup(name, description, source);if(selected?.length)await useStockGroups.getState().syncRemote(); onSaved(mode === 'add' ? 'Stock group was added' : 'Stock group was updated', item); onClose(); } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to save stock group.'); } finally {setPending(false);} };
  return <div className="stock-groups-flow"><Modal title={`${mode === 'add' ? 'Add' : 'Edit'} stocks group`} width={700} onClose={()=>{if(!pending)onClose();}} footer={<><Button disabled={pending} onClick={onClose}>Close</Button><Button className="primary" disabled={pending} onClick={()=>void save()}>Save</Button></>}>
    {error && <p className="stock-group-error" role="alert">{error}</p>}
    {selected?.length&&<p>Apply the description to {selected.length} selected groups.</p>}<Field label="Group name *"><TextInput disabled={pending||Boolean(selected?.length)} value={name} maxLength={50} autoFocus onChange={event => setName(event.target.value)}/></Field>
    <Field label="Description"><textarea aria-label="Description" disabled={pending} className="text-input stock-group-description" value={description} maxLength={250} onChange={event => setDescription(event.target.value)}/></Field>
  </Modal></div>;
}
