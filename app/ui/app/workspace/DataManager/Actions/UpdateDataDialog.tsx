import { useState } from 'react';
import { Button, Field, Modal, TextInput } from '../../../components/ui';

/** Explicit initial history range; acquisition remains a backend operation. */
export function UpdateDataDialog({ onClose, onStart }: { onClose: () => void; onStart: (range: { date_from: string; date_to: string }) => Promise<void> }) {
  const [from, setFrom] = useState('');
  const [to, setTo] = useState(new Date().toISOString().slice(0, 10));
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  async function start() {
    if (!from || !to || from > to) { setError('Choose a valid initial history range.'); return; }
    setBusy(true); setError('');
    try { await onStart({ date_from: from, date_to: to }); onClose(); }
    catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to submit updates.'); }
    finally { setBusy(false); }
  }
  return <Modal title="Download / update history" width={480} onClose={onClose} footer={<><Button disabled={busy} onClick={onClose}>Close</Button><Button disabled={busy} onClick={() => void start()}>{busy ? 'Submitting…' : 'Start download'}</Button></>}>
    <p>Choose the range to acquire from the selected data source. Existing rows follow that source’s update policy.</p>
    <Field label="Date from"><TextInput type="date" value={from} onChange={event => setFrom(event.target.value)} /></Field>
    <Field label="Date to"><TextInput type="date" value={to} onChange={event => setTo(event.target.value)} /></Field>
    {error && <p role="alert">{error}</p>}
  </Modal>;
}
