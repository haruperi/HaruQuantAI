import { useEffect, useRef, useState, type InputHTMLAttributes } from 'react';
import { Button, TextInput } from '../../../components/ui';
import { discoverTD, type TDManifest } from './tickDownloader';
import { useTickDownloader } from './tickDownloaderStore';
import './tickDownloader.css';

export function TickDownloaderImportDialog({ onClose, onStarted }: { onClose: () => void; onStarted: () => void }) {
  const saved = useTickDownloader();
  const [manifest, setManifest] = useState<TDManifest | null>(null);
  const [postfix, setPostfix] = useState(saved.postfix);
  const [selected, setSelected] = useState<string[]>([]);
  const [error, setError] = useState('');
  const picker = useRef<HTMLInputElement>(null);
  const root = useRef<HTMLDivElement>(null);
  const allCheck = useRef<HTMLInputElement>(null);
  const symbols = manifest?.symbols ?? [];
  const all = symbols.length > 0 && selected.length === symbols.length;
  useEffect(() => { if (allCheck.current) allCheck.current.indeterminate = selected.length > 0 && !all; }, [all, selected]);
  useEffect(() => { const previous = document.activeElement as HTMLElement | null; root.current?.querySelector<HTMLButtonElement>('button')?.focus(); return () => previous?.focus(); }, []);
  function start() {
    try {
      if (!manifest) throw new Error('Select a TickDownloader installation folder.');
      saved.start({ folder: manifest.folder, symbols: selected, postfix }, symbols);
      onStarted(); onClose();
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to import data.'); }
  }
  return <div className="modal-backdrop"><div ref={root} className="modal td-import-dialog" role="dialog" aria-modal="true" aria-labelledby="td-import-title" onKeyDown={event => {
    if (event.key === 'Escape') { event.stopPropagation(); onClose(); }
    if (event.key === 'Tab') {
      const controls = Array.from(root.current?.querySelectorAll<HTMLElement>('button:not(:disabled),input:not(:disabled):not([type=file])') ?? []);
      const first = controls[0]; const last = controls.at(-1);
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
    }
  }}>
    <header><h2 id="td-import-title">Import data from TickDownloader</h2><button className="icon-button" aria-label="Close" onClick={onClose}>×</button></header>
    <div className="modal-content">
      {(error || saved.storageError) && <p className="td-import-error" role="alert">{error || saved.storageError}</p>}
      <fieldset>
        <p className="td-import-help">If you have TickDownloader installation you can import the data directly from the TD downloaded data folders.<br/>Please select your TickDownloader installation folder below.</p>
        <div className="td-directory"><label htmlFor="td-folder">TickDownloader Installation</label><TextInput id="td-folder" readOnly value={manifest?.folder ?? saved.folder}/><button className="td-select-link" onClick={() => picker.current?.click()}>Select</button>
          <input ref={picker} type="file" aria-label="Select TickDownloader data folder" hidden {...({ webkitdirectory: '', directory: '' } as InputHTMLAttributes<HTMLInputElement>)} onChange={event => {
            if (!event.target.files?.length) return;
            setError(''); setSelected([]); setManifest(null);
            try { setManifest(discoverTD(Array.from(event.target.files, file => file.webkitRelativePath))); }
            catch (cause) { setError(cause instanceof Error ? cause.message : 'Cannot load available symbols.'); }
            event.target.value = '';
          }}/>
        </div>
        {!manifest && saved.folder && <small className="td-reselect">Select the folder again to access its available symbols.</small>}
        <div className="td-symbol-grid"><table aria-label="TickDownloader symbols"><thead><tr><th><input ref={allCheck} aria-label="Select all TickDownloader symbols" type="checkbox" checked={all} disabled={!symbols.length} onChange={() => setSelected(all ? [] : symbols)}/></th><th>Symbol</th></tr></thead><tbody>{symbols.map(symbol => <tr key={symbol} className={selected.includes(symbol) ? 'selected' : ''}><td><input type="checkbox" aria-label={`Select symbol ${symbol}`} checked={selected.includes(symbol)} onChange={() => setSelected(current => current.includes(symbol) ? current.filter(item => item !== symbol) : [...current, symbol])}/></td><td>{symbol}</td></tr>)}{!symbols.length && <tr><td colSpan={2}>No symbols available.</td></tr>}</tbody></table></div>
        <div className="td-postfix"><label htmlFor="td-postfix">Data postfix</label><div><TextInput id="td-postfix" value={postfix} onChange={event => { setPostfix(event.target.value); setError(''); }}/><small>This postfix will be optionally added to the data names created</small></div></div>
      </fieldset>
    </div>
    <footer><Button onClick={onClose}>Close</Button><Button className="primary" onClick={start}>Start import</Button></footer>
  </div></div>;
}
