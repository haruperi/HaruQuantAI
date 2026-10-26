import { useRef, useState } from 'react';
import { Button, Field, Modal, TextInput } from '../../../../components/ui';
import { type SessionDefinition, type SessionBroker } from './sessions';
import { loadSessionJson, saveSessionJson } from './sessionApiClient';
import { useSessions } from './sessionStore';
import './sessions.css';

export function SessionTransferDialog({ mode, onClose, onSaved }: {
  mode: 'save' | 'load'; selected: SessionDefinition[]; all: SessionDefinition[]; brokers: SessionBroker[];
  onClose: () => void; onSaved: (message: string) => void;
}) {
  const [filename, setFilename] = useState('Sessions.json');
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState('');
  const [report, setReport] = useState('');
  const [pending, setPending] = useState(false);
  const busy = useRef(false);
  const close = () => { if (!busy.current) onClose(); };
  async function transfer() {
    if (busy.current) return;
    busy.current = true; setPending(true); setError(''); setReport('');
    const epoch = useSessions.getState().epoch;
    try {
      if (mode === 'load') {
        if (!file || !file.name.toLowerCase().endsWith('.json')) throw new Error('Choose a JSON file.');
        if (file.size > 10_000_000) throw new Error('Choose a JSON file up to 10 MB.');
        const result = await loadSessionJson(await file.text());
        if (epoch !== useSessions.getState().epoch) return;
        await useSessions.getState().refreshFromServer();
        const message = `Loaded ${result.loaded_count} sessions.`;
        setReport(message); onSaved(message);
      } else {
        const result = await saveSessionJson();
        if (epoch !== useSessions.getState().epoch) return;
        const url = URL.createObjectURL(new Blob([result.content], { type: 'application/json;charset=utf-8' }));
        const anchor = document.createElement('a');
        anchor.href = url; anchor.download = /^[^\\/:*?"<>|]+\.json$/i.test(filename) ? filename : 'Sessions.json';
        anchor.click(); window.setTimeout(() => URL.revokeObjectURL(url), 1000);
        onSaved(`Saved ${result.count} sessions to JSON.`); onClose();
      }
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to transfer sessions.'); }
    finally { busy.current = false; setPending(false); }
  }
  return <div className="sessions-flow"><Modal title={mode === 'save' ? 'Save sessions' : 'Load sessions'} width={560} onClose={close} footer={<><Button disabled={pending} onClick={close}>Close</Button><Button disabled={pending || (mode === 'load' && !file)} onClick={() => void transfer()}>{pending ? 'Working…' : mode === 'save' ? 'Download JSON' : 'Load JSON'}</Button></>}>
    {error && <p role="alert">{error}</p>}{report && <p role="status">{report}</p>}
    {mode === 'save' ? <><p>Export all persisted session profiles, intervals, and holidays.</p><Field label="File name"><TextInput disabled={pending} value={filename} onChange={event => setFilename(event.target.value)}/></Field></> : <><p>Import a JSON array of sessions. Duplicate names or invalid entries cancel the whole import.</p><Field label="JSON file"><input type="file" accept=".json,application/json" disabled={pending} onChange={event => setFile(event.target.files?.[0] ?? null)}/></Field></>}
  </Modal></div>;
}
