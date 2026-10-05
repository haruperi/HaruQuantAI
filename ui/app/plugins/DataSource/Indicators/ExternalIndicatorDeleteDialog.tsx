import { useState } from 'react';
import { Button, Modal } from '../../../components/ui';
import { useExternalIndicators } from './externalIndicatorsStore';
import './externalIndicators.css';

export function ExternalIndicatorDeleteDialog({ names, onClose, onSaved }: { names: string[]; onClose: () => void; onSaved: (message: string) => void }) {
  const store = useExternalIndicators(); const [error, setError] = useState(''); const question = names.length > 1 ? `Do you want to remove selected indicators (${names.length}) or only clear their data ?` : `Do you want to remove indicator '${names[0]}' or only clear its data ?`;
  async function act(kind: 'clear' | 'delete'): Promise<void> { try { kind === 'clear' ? await store.clear(names) : await store.remove(names); onSaved(kind === 'clear' ? 'Indicator data cleared.' : 'Indicator removed.'); onClose(); } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to change indicator.'); } }
  return <div className="external-flow"><Modal title="Delete custom data" width={600} onClose={onClose} footer={<><Button onClick={onClose}>Close</Button><Button className="primary" onClick={() => act('clear')}>Clear data</Button><Button className="danger" onClick={() => act('delete')}>Delete</Button></>}>
    {(error || store.storageError) && <p className="external-error" role="alert">{error || store.storageError}</p>}<p>{question}</p>
  </Modal></div>;
}
