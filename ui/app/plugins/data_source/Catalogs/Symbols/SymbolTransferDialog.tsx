import { useState } from 'react';
import { Button, Field, Modal, TextInput } from '../../../../components/ui';
import { serializeSymbolsJson, type FileSymbol, type SymbolBroker } from '../../FileImport/fileSymbols';
import './symbols.css';

export function SymbolTransferDialog({ mode, selected, brokers, onClose, onSaved }: {
  mode: 'save' | 'load'; selected: FileSymbol[]; all: FileSymbol[]; brokers: SymbolBroker[];
  onClose: () => void; onSaved: (message: string) => void;
}) {
  const [fileName, setFileName] = useState('Symbols.json');
  const [error, setError] = useState('');
  function download() {
    try {
      if (mode !== 'save') throw new Error('Symbol import is not implemented.');
      if (!selected.length) throw new Error('Select at least one symbol.');
      const content = serializeSymbolsJson(selected, brokers);
      const url = URL.createObjectURL(new Blob([content], { type: 'application/json' }));
      const anchor = document.createElement('a');
      anchor.href = url; anchor.download = /^[^\\/:*?"<>|]+\.json$/i.test(fileName) ? fileName : 'Symbols.json';
      anchor.click(); window.setTimeout(() => URL.revokeObjectURL(url), 1000);
      onSaved('Symbols exported.'); onClose();
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to export symbols.'); }
  }
  return <div className="symbols-flow"><Modal title={mode === 'save' ? 'Save symbols' : 'Load symbols'} width={560} onClose={onClose} footer={<><Button onClick={onClose}>Close</Button>{mode === 'save' && <Button onClick={download}>Download JSON</Button>}</>}>
    {error && <p role="alert">{error}</p>}
    {mode === 'save' ? <><p>Export {selected.length} selected symbol specifications.</p><Field label="File name"><TextInput value={fileName} onChange={event => setFileName(event.target.value)}/></Field></> : <p>Symbol import is not implemented.</p>}
  </Modal></div>;
}
