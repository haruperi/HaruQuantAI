import type { InputHTMLAttributes } from 'react';
import { Button, TextInput } from '../../../../components/ui';
import { DarwinexModal } from '../add/addPopup';
import { useImportPopup } from './importPopupCtrl';

export function ImportPopup({ onClose, onStarted }: { onClose: () => void; onStarted: () => void }) {
  const { store, picker, manifest, selected, setSelected, postfix, setPostfix, error, setError, symbols, start, chooseFolder } = useImportPopup(onClose, onStarted);
  return <DarwinexModal title="Import data from Darwinex" onClose={onClose} footer={<><Button onClick={onClose}>Close</Button><Button className="primary" onClick={start}>Start import</Button></>}>
    {(error || store.storageError) && <p role="alert" className="darwinex-error">{error || store.storageError}</p>}
    <fieldset><div className="darwinex-folder"><label htmlFor="darwinex-folder">Darwinex data folder</label><TextInput id="darwinex-folder" readOnly value={manifest?.folder ?? store.folder}/><Button onClick={() => picker.current?.click()}>Select</Button><input ref={picker} hidden type="file" aria-label="Select Darwinex data folder" {...({ webkitdirectory: '', directory: '' } as InputHTMLAttributes<HTMLInputElement>)} onChange={chooseFolder}/></div>
    {!manifest && store.folder && <p>Select the folder again to access its available symbols.</p>}
    <div className="darwinex-grid"><table className="plain-table" aria-label="Darwinex import symbols"><thead><tr><th><input aria-label="Select all import symbols" type="checkbox" checked={symbols.length > 0 && selected.length === symbols.length} disabled={!symbols.length} onChange={() => setSelected(selected.length === symbols.length ? [] : symbols)}/></th><th>Symbol</th></tr></thead><tbody>{symbols.map(symbol => <tr key={symbol}><td><input type="checkbox" aria-label={`Select symbol ${symbol}`} checked={selected.includes(symbol)} onChange={() => setSelected(current => current.includes(symbol) ? current.filter(item => item !== symbol) : [...current,symbol])}/></td><td>{symbol}</td></tr>)}{!symbols.length && <tr><td colSpan={2}>No symbols available.</td></tr>}</tbody></table></div><label className="darwinex-postfix">Data postfix <TextInput aria-label="Data postfix" maxLength={64} value={postfix} onChange={event => setPostfix(event.target.value)}/><small>This postfix will be optionally added to the data names created</small></label></fieldset>
  </DarwinexModal>;
}
