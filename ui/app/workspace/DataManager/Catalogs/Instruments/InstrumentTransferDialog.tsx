import { useState } from 'react';
import { Button, Field, Modal, TextInput } from '../../../../components/ui';
import { parseInstrumentsJson, serializeInstrumentsJson, type FileInstrument, type InstrumentBroker } from './fileSymbols';
import { useFileSymbols } from './fileSymbolsStore';
import './instruments.css';
function download(name: string, content: string): void { const url = URL.createObjectURL(new Blob([content], { type: 'application/json' })); const anchor = document.createElement('a'); anchor.href = url; anchor.download = name; anchor.click(); window.setTimeout(() => URL.revokeObjectURL(url), 1000); }
export function InstrumentTransferDialog({ mode, selected, all, brokers, onClose, onSaved }: {
    mode: 'save' | 'load';
    selected: FileInstrument[];
    all: FileInstrument[];
    brokers: InstrumentBroker[];
    onClose: () => void;
    onSaved: (message: string) => void;
}) {
    const store = useFileSymbols();
    const [fileName, setFileName] = useState('Instruments.json');
    const [file, setFile] = useState<File | null>(null);
    const [error, setError] = useState('');
    const [pending, setPending] = useState<FileInstrument[]>([]);
    const [conflicts, setConflicts] = useState<string[]>([]);
    const [index, setIndex] = useState(0);
    const [skipped, setSkipped] = useState<string[]>([]);
    const [overwrite, setOverwrite] = useState<string[]>([]);
    async function commit(items = pending, overwriteNames = overwrite, skippedNames = skipped): Promise<void> {
        try {
            await store.importInstruments(items.filter(item => !skippedNames.includes(item.symbol)), overwriteNames, brokers.map(row => row.id));
            onSaved(`Instruments (${items.length - skippedNames.length}) loaded.`);
            onClose();
        }
        catch (cause) {
            setError(cause instanceof Error ? cause.message : 'Cannot load instruments.');
        }
    }
    async function decide(action: 'skip' | 'overwrite' | 'overwrite-all'): Promise<void> {
        const name = conflicts[index];
        const nextSkipped = action === 'skip' ? [...skipped, name] : skipped;
        const nextOverwrite = action === 'skip' ? overwrite : action === 'overwrite-all' ? [...overwrite, ...conflicts.slice(index)] : [...overwrite, name];
        if (action === 'overwrite-all' || index === conflicts.length - 1)
            await commit(pending, nextOverwrite, nextSkipped);
        else {
            setSkipped(nextSkipped);
            setOverwrite(nextOverwrite);
            setIndex(value => value + 1);
        }
    }
    async function primary(): Promise<Promise<void>> {
        try {
            setError('');
            if (mode === 'save') {
                if (!selected.length)
                    throw new Error('You have to select at least one instrument.');
                const safe = /^[^\\/:*?"<>|]+\.json$/i.test(fileName) ? fileName : 'Instruments.json';
                download(safe, serializeInstrumentsJson(selected, brokers));
                onSaved('Instruments saved.');
                onClose();
                return;
            }
            if (!file)
                throw new Error('Select an Instruments JSON file.');
            if (file.size > 2000000)
                throw new Error('Instrument file is too large.');
            const items = parseInstrumentsJson(await file.text(), brokers);
            const duplicate = items.map(item => all.find(row => row.symbol.toLowerCase() === item.symbol.toLowerCase())?.symbol).filter((name): name is string => Boolean(name));
            setPending(items);
            setConflicts(duplicate);
            setIndex(0);
            setSkipped([]);
            setOverwrite([]);
            if (!duplicate.length)
                await commit(items, [], []);
        }
        catch (cause) {
            setError(cause instanceof Error ? cause.message : 'Cannot load instruments.');
        }
    }
    if (mode === 'load' && conflicts.length)
        return <div className="instruments-flow"><Modal title="Overwrite confirm" width={560} onClose={onClose} footer={<><Button onClick={onClose}>Cancel</Button><Button onClick={async () => await decide('skip')}>Skip</Button><Button onClick={async () => await decide('overwrite')}>Overwrite</Button><Button className="primary" onClick={async () => await decide('overwrite-all')}>Overwrite all</Button></>}><p>Instrument '{conflicts[index]}' already exists, do you want to overwrite it with the imported one?</p><p className="instrument-conflict-count">Conflict {index + 1} of {conflicts.length}</p></Modal></div>;
    return <div className="instruments-flow"><Modal title={mode === 'save' ? 'Save instruments' : 'Load instruments'} width={560} onClose={onClose} footer={<><Button onClick={onClose}>Close</Button><Button className="primary" onClick={async () => void await primary()}>{mode === 'save' ? 'Download JSON' : 'Validate and load'}</Button></>}>
    {(error || store.storageError) && <p role="alert" className="instrument-error">{error || store.storageError}</p>}
    {mode === 'save' ? <><p>Export <strong>{selected.length}</strong> selected instrument{selected.length === 1 ? '' : 's'} and required broker metadata.</p><Field label="File name"><TextInput value={fileName} onChange={event => setFileName(event.target.value)}/></Field></> : <><Field label="Instrument JSON file"><input aria-label="Instrument JSON file" className="file-input compact" type="file" accept=".json,application/json" onChange={event => { setFile(event.target.files?.[0] ?? null); setError(''); }}/></Field><p className="instrument-note">The complete file is validated before any browser-local instrument is changed.</p></>}
  </Modal></div>;
}
