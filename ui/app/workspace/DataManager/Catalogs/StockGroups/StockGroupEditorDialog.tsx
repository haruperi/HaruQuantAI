import { useState } from 'react';
import { Button, Field, Modal, TextInput } from '../../../../components/ui';
import { useStockGroups } from './stockGroupsStore';
import type { StockGroupDefinition } from './stockGroups';
import './stockGroups.css';
export function StockGroupEditorDialog({ mode, source, onClose, onSaved }: {
    mode: 'add' | 'edit';
    source?: StockGroupDefinition;
    onClose: () => void;
    onSaved: (message: string, item: StockGroupDefinition) => void;
}) {
    const [name, setName] = useState(source?.name ?? '');
    const [description, setDescription] = useState(source?.description ?? '');
    const [error, setError] = useState('');
    const save = async () => {
        try {
            const item = await useStockGroups.getState().saveGroup(name, description, source);
            onSaved(mode === 'add' ? 'Stock group was added' : 'Stock group was updated', item);
            onClose();
        }
        catch (cause) {
            setError(cause instanceof Error ? cause.message : 'Unable to save stock group.');
        }
    };
    return <div className="stock-groups-flow"><Modal title={`${mode === 'add' ? 'Add' : 'Edit'} stocks group`} width={700} onClose={onClose} footer={<><Button onClick={onClose}>Close</Button><Button className="primary" onClick={save}>Save</Button></>}>
    {error && <p className="stock-group-error" role="alert">{error}</p>}
    <Field label="Group name *"><TextInput value={name} maxLength={50} autoFocus onChange={event => setName(event.target.value)}/></Field>
    <Field label="Description"><textarea className="text-input stock-group-description" value={description} maxLength={250} onChange={event => setDescription(event.target.value)}/></Field>
  </Modal></div>;
}
