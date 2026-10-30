import { filesService } from '../../FileImport/DataSourceFilesService';
import { emptyFileRecord } from '../../FileImport/fileImport';
import { newSymbol } from '../../FileImport/fileSymbols';
import { useRef, useState, type ChangeEvent } from 'react';
import type { DarwinexManifest } from '../darwinex';
import { useDarwinex } from '../darwinexStore';
import { darwinexService } from '../DarwinexService';

export function useImportPopup(onClose: () => void, onStarted: () => void) {
  const chosenFiles = useRef<File[]>([]);
  const store = useDarwinex(); const picker = useRef<HTMLInputElement>(null);
  const [manifest, setManifest] = useState<DarwinexManifest | null>(null), [selected, setSelected] = useState<string[]>([]), [postfix, setPostfix] = useState(store.postfix), [error, setError] = useState('');
  const symbols = manifest?.symbols ?? [];
  async function start() { try {
    if (!manifest || !selected.length) throw new Error('Select downloaded Darwinex files and symbols.');
    const tasks = chosenFiles.current.flatMap(file=>{const symbol=selected.find(name=>(file.webkitRelativePath || file.name).toUpperCase().includes(name.toUpperCase())); return symbol && /\.(dat|csv|txt|gz|zip|parquet)$/i.test(file.name) ? [{file,filename:file.name,provider:'darwinex',ignored:0,record:{...emptyFileRecord(symbol+postfix,newSymbol(),'start'),underlying:symbol,timeframe:'auto',timestamps:[],unknownBars:0}}] : [];});
    await filesService.start(tasks,'UTC','',0); onStarted(); onClose();
  } catch(cause) {setError(String(cause));} }

  const chooseFolder = (event: ChangeEvent<HTMLInputElement>) => { if (!event.target.files?.length) return; chosenFiles.current=Array.from(event.target.files); setSelected([]); setManifest(null); setError(''); try { setManifest(darwinexService.discover(Array.from(event.target.files, file => file.webkitRelativePath))); } catch (cause) { setError(cause instanceof Error ? cause.message : 'Cannot load symbols.'); } event.target.value = ''; };
  return { store, picker, manifest, selected, setSelected, postfix, setPostfix, error, setError, symbols, start, chooseFolder };
}
