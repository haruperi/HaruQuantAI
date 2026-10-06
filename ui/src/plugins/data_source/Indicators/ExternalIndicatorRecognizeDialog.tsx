import { useState } from 'react';
import { Button, Field, Modal, TextInput } from '../../../components/ui';
import { recognizeMq4, type ExternalIndicatorDefinition } from './externalIndicators';
import { useExternalIndicators } from './externalIndicatorsStore';
import './externalIndicators.css';

export function ExternalIndicatorRecognizeDialog({ onClose, onSaved }: { onClose: () => void; onSaved: (message: string) => void }) {
  const store = useExternalIndicators(); const [file, setFile] = useState<File | null>(null); const [recognized, setRecognized] = useState<ExternalIndicatorDefinition | null>(null); const [error, setError] = useState('');
  async function choose(next: File | null): Promise<void> { setFile(next); setRecognized(null); setError(''); if (!next) return; try { if (next.size > 2_000_000) throw new Error('Maximum MQ4 file size is 2 MiB.'); const bytes = await next.arrayBuffer(); const text = new TextDecoder('utf-8', { fatal: true }).decode(bytes); setRecognized(recognizeMq4(next.name, text)); } catch (cause) { setError(cause instanceof Error ? cause.message : 'Failed to recognize custom indicator from file.'); } }
  function save(): void { try { if (!recognized) throw new Error('Select a valid MQ4 indicator file.'); store.add(recognized); onSaved(`Indicator '${recognized.name}' added.`); onClose(); } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to add indicator.'); } }
  return <div className="external-flow"><Modal title="Recognize from file" width={650} onClose={onClose} footer={<><Button onClick={onClose}>Close</Button><Button className="primary" disabled={!recognized} onClick={save}>Save</Button></>}>
    {(error || store.storageError) && <p className="external-error" role="alert">{error || store.storageError}</p>}
    <fieldset><legend>Select custom indicator file</legend><Field label="MQ4 file"><input className="file-input compact" aria-label="MQ4 file" type="file" accept=".mq4,text/plain" onChange={event => void choose(event.target.files?.[0] ?? null)}/></Field></fieldset>
    <fieldset><legend>Recognized indicator</legend>{recognized ? <div className="external-two"><Field label="Name"><TextInput value={recognized.name} readOnly/></Field><Field label="Output lines"><TextInput value={recognized.values.filter(line => line.name).map(line => line.name).join(', ')} readOnly/></Field></div> : <p className="external-note">{file ? 'Reading indicator metadata…' : 'No file selected.'}</p>}</fieldset>
    <p className="external-note">The browser reads metadata only. MQ4 source is never compiled or executed.</p>
  </Modal></div>;
}
