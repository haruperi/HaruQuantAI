import { useState } from 'react';
import { Button, Field, Modal, TextInput } from '../../../../components/ui';
import { serializeInstrumentsJson, type FileInstrument, type InstrumentBroker } from '../../FileImport/fileSymbols';
import './instruments.css';

export function InstrumentTransferDialog({ mode, selected, brokers, onClose, onSaved }: {
  mode: 'save' | 'load'; selected: FileInstrument[]; all: FileInstrument[]; brokers: InstrumentBroker[];
  onClose: () => void; onSaved: (message: string) => void;
}) {
  const [fileName, setFileName] = useState('Instruments.json');
  const [error, setError] = useState('');
  function download() {
    try {
      if (mode !== 'save') throw new Error('Instrument import is not implemented.');
      if (!selected.length) throw new Error('Select at least one instrument.');
      const content = serializeInstrumentsJson(selected, brokers);
      const url = URL.createObjectURL(new Blob([content], { type: 'application/json' }));
      const anchor = document.createElement('a');
      anchor.href = url; anchor.download = /^[^\\/:*?"<>|]+\.json$/i.test(fileName) ? fileName : 'Instruments.json';
      anchor.click(); window.setTimeout(() => URL.revokeObjectURL(url), 1000);
      onSaved('Instruments exported.'); onClose();
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to export instruments.'); }
  }
  return <div className="instruments-flow"><Modal title={mode === 'save' ? 'Save instruments' : 'Load instruments'} width={560} onClose={onClose} footer={<><Button onClick={onClose}>Close</Button>{mode === 'save' && <Button onClick={download}>Download JSON</Button>}</>}>
    {error && <p role="alert">{error}</p>}
    {mode === 'save' ? <><p>Export {selected.length} selected instrument specifications.</p><Field label="File name"><TextInput value={fileName} onChange={event => setFileName(event.target.value)}/></Field></> : <p>Instrument import is not implemented.</p>}
  </Modal></div>;
}
