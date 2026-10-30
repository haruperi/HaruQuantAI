import { useRef, useState } from 'react';
import { Button, Field, Modal, TextInput } from '../../../../../common/components/ui';
import type { FileSymbol, SymbolBroker } from '../../FileImport/fileSymbols';
import { loadSymbolCsv, saveSymbolCsv } from './symbolsApiClient';
import { useSymbols } from './symbolsStore';
import './symbols.css';

export function SymbolTransferDialog({ mode, selected, all, onClose, onSaved }: {
  mode: 'save' | 'load'; selected: FileSymbol[]; all: FileSymbol[]; brokers: SymbolBroker[];
  onClose: () => void; onSaved: (message: string) => void;
}) {
  const [fileName, setFileName] = useState('Symbols.csv');
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState('');
  const [report, setReport] = useState('');
  const [busy, setBusy] = useState(false);
  const submitting = useRef(false);
  const targets = selected.length ? selected : all;
  const close = () => { if (!submitting.current) onClose(); };
  async function transfer() {
    if (submitting.current) return;
    submitting.current = true; setBusy(true); setError(''); setReport('');
    try {
      if (mode === 'load') {
        if (!file || !file.name.toLowerCase().endsWith('.csv')) throw new Error('Choose a CSV file.');
        if (file.size > 10_000_000) throw new Error('Choose a CSV file up to 10 MB.');
        const result = await loadSymbolCsv(await file.text());
        await useSymbols.getState().refreshFromServer();
        const message = `Loaded ${result.loaded_count} of ${result.total} symbols.`;
        setReport(message + result.errors.map(item => `\nSkipped row ${item.row}: ${item.error}`).join(''));
        onSaved(message);
      } else {
        const result = await saveSymbolCsv(selected.map(item => item.id).filter((id): id is string => Boolean(id)));
        const url = URL.createObjectURL(new Blob(['\ufeff', result.content], { type: 'text/csv;charset=utf-8' }));
        const anchor = document.createElement('a');
        anchor.href = url; anchor.download = /^[^\\/:*?"<>|]+\.csv$/i.test(fileName) ? fileName : 'Symbols.csv';
        anchor.click(); window.setTimeout(() => URL.revokeObjectURL(url), 1000);
        onSaved(`Saved ${result.count} symbols to CSV.`); onClose();
      }
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to transfer symbols.'); }
    finally { submitting.current = false; setBusy(false); }
  }
  return <div className="symbols-flow"><Modal title={mode === 'save' ? 'Save symbols' : 'Load symbols'} width={560} onClose={close} footer={<><Button disabled={busy} onClick={close}>Close</Button><Button disabled={busy || (mode === 'load' && !file) || (mode === 'save' && !targets.length)} onClick={() => void transfer()}>{busy ? 'Working…' : mode === 'save' ? 'Download CSV' : 'Load CSV'}</Button></>}>
    {error && <p role="alert">{error}</p>}
    {report && <pre role="status" style={{ whiteSpace: 'pre-wrap' }}>{report}</pre>}
    {mode === 'save' ? <><p>Export {selected.length ? `${selected.length} selected` : 'all'} symbol specifications.</p><Field label="File name"><TextInput disabled={busy} value={fileName} onChange={event => setFileName(event.target.value)}/></Field></> : <><p>Choose a symbol CSV file. Valid rows are imported; duplicates and invalid rows are reported.</p><Field label="CSV file"><input type="file" accept=".csv,text/csv" disabled={busy} onChange={event => setFile(event.target.files?.[0] ?? null)}/></Field></>}
  </Modal></div>;
}
