import type { InputHTMLAttributes } from 'react';
import { Button, TextInput } from '../../../../components/ui';
import { useDataSourceTDImport, type TDImportCallbacks } from './DataSourceTDImportCtrl';
import '../styles.css';
export function TickDownloaderImportDialog(props: TDImportCallbacks) {
  const { onClose } = props;
  const { saved, manifest, postfix, selected, error, picker, root, allCheck, symbols, all, start, selectFolder, setSelected, setPostfix, setError } = useDataSourceTDImport(props);
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
          <input ref={picker} type="file" aria-label="Select TickDownloader data folder" hidden {...({ webkitdirectory: '', directory: '' } as InputHTMLAttributes<HTMLInputElement>)} onChange={selectFolder}/>
        </div>
        {!manifest && saved.folder && <small className="td-reselect">Select the folder again to access its available symbols.</small>}
        <div className="td-symbol-grid"><table aria-label="TickDownloader symbols"><thead><tr><th><input ref={allCheck} aria-label="Select all TickDownloader symbols" type="checkbox" checked={all} disabled={!symbols.length} onChange={() => setSelected(all ? [] : symbols)}/></th><th>Symbol</th></tr></thead><tbody>{symbols.map(symbol => <tr key={symbol} className={selected.includes(symbol) ? 'selected' : ''}><td><input type="checkbox" aria-label={`Select symbol ${symbol}`} checked={selected.includes(symbol)} onChange={() => setSelected(current => current.includes(symbol) ? current.filter(item => item !== symbol) : [...current, symbol])}/></td><td>{symbol}</td></tr>)}{!symbols.length && <tr><td colSpan={2}>No symbols available.</td></tr>}</tbody></table></div>
        <div className="td-postfix"><label htmlFor="td-postfix">Data postfix</label><div><TextInput id="td-postfix" value={postfix} onChange={event => { setPostfix(event.target.value); setError(''); }}/><small>This postfix will be optionally added to the data names created</small></div></div>
      </fieldset>
    </div>
    <footer><Button onClick={onClose}>Close</Button><Button className="primary" onClick={start}>Start import</Button></footer>
  </div></div>;
}
