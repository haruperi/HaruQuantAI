import { Field, TextInput } from '../../../../components/ui';

/** Controlled name fields; save/cancel and validation belong to import controller. */
export function NewFormatPopup({ name, onNameChange }: { name: string; onNameChange: (name: string) => void }) {
  return <><p>Enter name for the new data format.</p><Field label="Name"><TextInput value={name} maxLength={80} onChange={event => onNameChange(event.target.value)}/></Field></>;
}
